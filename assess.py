"""Local research CLI. Inputs and outputs stay in memory unless explicitly redirected."""
import argparse
import copy
import json
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MAX_CHARS=4000
SCHEMA=json.loads((ROOT/'model'/'assessment-response.schema.json').read_text(encoding='utf-8-sig'))

def check_input(data):
    if data.get('reviewed') is not True:
        raise ValueError('Review speakers, turns and argument groupings, then set reviewed=true.')
    turns=data.get('turns')
    if not isinstance(turns,list) or not turns:
        raise ValueError('Supply a nonempty turns list.')
    ids=set()
    for turn in turns:
        for key in ['turn_id','speaker_id','speaker_label','text']:
            if not isinstance(turn.get(key),str) or not turn[key].strip():
                raise ValueError(f'Each turn needs a nonempty {key}.')
        if turn['turn_id'] in ids: raise ValueError('Duplicate turn ID.')
        ids.add(turn['turn_id'])
        # Optional reviewed argument groups are exact substrings, never cross-turn.
        if 'argument_groups' in turn:
            if not isinstance(turn['argument_groups'],list): raise ValueError('Groups must be a list.')
            for excerpt in turn['argument_groups']:
                if not isinstance(excerpt,str) or not excerpt or excerpt not in turn['text']:
                    raise ValueError('Reviewed argument group must be an exact excerpt of its turn.')
    if not isinstance(data.get('context',''),str): raise ValueError('Context must be text.')
    size=sum(len(t['text']) for t in turns)+len(data.get('context',''))
    if size>MAX_CHARS: raise ValueError(f'Input exceeds {MAX_CHARS} characters; shorten it. Nothing was analyzed.')
    for turn in turns:
        if 'counterargument_turn_ids' in turn:
            refs=turn['counterargument_turn_ids']
            if not isinstance(refs,list) or any(r not in ids or r==turn['turn_id'] for r in refs):
                raise ValueError('Invalid reviewed counterargument turn references.')
    return data

def validate_response(data, result):
    from jsonschema import Draft202012Validator
    Draft202012Validator(SCHEMA).validate(result)
    source=data['turns']
    if len(result['turns'])!=len(source): raise ValueError('Model omitted or added turns.')
    arg_ids={}
    participants={}
    adjustments=[]
    for original, turn in zip(source,result['turns']):
        if any(original[k]!=turn[k] for k in ['turn_id','speaker_id']):
            raise ValueError('Model changed turn order or speaker identities.')
        scores=participants.setdefault(original['speaker_id'],[])
        if turn['status']=='not_assessable':
            if original.get('argument_groups'): raise ValueError('Model omitted reviewed argument groups.')
            continue
        args=turn['arguments']
        if 'argument_groups' in original and [a['argument_excerpt'] for a in args]!=original['argument_groups']:
            raise ValueError('Model changed reviewed argument groupings.')
        for a in args:
            aid=a['argument_id']
            if aid in arg_ids: raise ValueError('Duplicate argument ID.')
            arg_ids[aid]=(turn['speaker_id'],a)
            if a['argument_excerpt'] not in original['text']: raise ValueError('Argument excerpt is not from its turn.')
            for e in a['evidence']:
                if not any(e['quote'] in t['text'] for t in source): raise ValueError('Fabricated evidence quotation.')
            c=a['criterion_scores']
            # An explicit reviewed empty list establishes that no counterargument exists.
            if original.get('counterargument_turn_ids')==[] and c['counterargument_handling']!=50:
                c['counterargument_handling']=50
                adjustments.append(f'{aid}: enforced neutral 50 for reviewed absence of counterarguments.')
            mean=sum(c.values())/4
            if a['overall_score']!=mean: adjustments.append(f'{aid}: recomputed arithmetic mean.')
            a['overall_score']=mean
            # No owner-calibrated bands yet; never invent cutoffs.
            a['score_band']=None
            scores.append(mean)
    strongest=result['conversation_summary']['strongest_arguments']
    seen=set()
    for item in strongest:
        sid=item['speaker_id']; aid=item['argument_id']
        if aid not in arg_ids or arg_ids[aid][0]!=sid or sid in seen:
            raise ValueError('Invalid strongest-argument reference.')
        seen.add(sid)
    if seen!={sid for sid,ss in participants.items() if ss}:
        raise ValueError('Summary must identify one strongest argument for each assessable participant.')
    averages=[{'speaker_id':sid,'assessable_arguments':len(ss),
               'average':sum(ss)/len(ss) if ss else None,'limited_sample':len(ss)==1,
               'status':'assessed' if ss else 'not enough assessable arguments'} for sid,ss in participants.items()]
    return {'assessment':result,'participants':averages,'arithmetic_adjustments':adjustments,
            'notice':'Experimental local assessment. Rubric validity and score bands are not calibrated.'}

def call_model(data):
    check_input(data)
    prompt=(ROOT/'model'/'argument-assessment.prompt.md').read_text(encoding='utf-8-sig')
    prompt+='\nWhen argument_groups is supplied, preserve exactly those excerpts and groupings. An empty list means not assessable. When counterargument_turn_ids is [], the counterargument score must be 50. No score-band rubric is calibrated; use null. A factual claim appearing in the transcript is NOT verification: explicitly call uncorroborated facts unverified. Greetings are not disagreements. If no disagreement is expressed, key_disagreements must be []. Do not restate numeric scores in prose. Be brief. /no_think'
    payload={'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(data)}],
             'temperature':0,'seed':731,'max_tokens':3000,'cache_prompt':False,
             'chat_template_kwargs':{'enable_thinking':False},
             'response_format':{'type':'json_schema','json_schema':{'name':'assessment','strict':True,'schema':SCHEMA}}}
    request=urllib.request.Request('http://127.0.0.1:8766/v1/chat/completions',
        data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=600) as response: raw=json.load(response)
    if raw['choices'][0].get('finish_reason')!='stop': raise ValueError('Incomplete model output; no partial assessment accepted.')
    result=json.loads(raw['choices'][0]['message']['content'])
    return validate_response(data,result)

def prepare(text):
    """Conservative draft parser; ambiguous unlabeled text requires explicit manual review."""
    if len(text)>MAX_CHARS: raise ValueError(f'Transcript exceeds {MAX_CHARS} characters; shorten it.')
    speakers={}; turns=[]
    for line in text.splitlines():
        if not line.strip(): continue
        if ':' not in line: raise ValueError('Cannot reliably detect speakers. Use one Speaker: text turn per line or supply reviewed JSON.')
        label,body=line.split(':',1)
        if not label.strip() or not body.strip(): raise ValueError('Empty speaker or turn.')
        sid=speakers.setdefault(label.strip(),f's{len(speakers)+1}')
        turns.append({'turn_id':f't{len(turns)+1}','speaker_id':sid,'speaker_label':label.strip(),'text':body.strip()})
    return {'reviewed':False,'context':'','turns':turns}

def quality(text):
    import joblib
    if not text.strip(): raise ValueError('Argument text is empty.')
    if len(text)>MAX_CHARS: raise ValueError('Argument exceeds input limit.')
    model=joblib.load(ROOT/'weights'/'ibm-quality.joblib')
    score=max(0.,min(1.,float(model.predict([text])[0])))
    return {'ibm_WA_prediction':score,'display_score':score*100,
            'notice':'Auxiliary IBM speech-suitability prediction; not the four-criterion score.',
            'distribution_warning': 'Long argument outside the short-argument training setting.' if len(text)>245 else None}

def main():
    parser=argparse.ArgumentParser(description=f'Local argument assessment; {MAX_CHARS}-character input limit. No transcript files are written.')
    parser.add_argument('command',choices=['prepare','quality','assess','challenge'])
    args=parser.parse_args()
    text=sys.stdin.read()
    if args.command=='prepare': out=prepare(text)
    elif args.command=='quality': out=quality(text)
    elif args.command=='assess':
        data=json.loads(text); out=call_model(data)
        out['auxiliary_ibm_scores']=[{'argument_id':a['argument_id'],**quality(a['argument_excerpt'])}
            for t in out['assessment']['turns'] for a in t.get('arguments',[])]
    else:
        request=json.loads(text)
        data=check_input(request['input'])
        challenge=request.get('challenge','').strip()
        if not challenge: raise ValueError('Supply a challenge explanation.')
        original=validate_response(data,copy.deepcopy(request['original']['assessment']))
        revised_input=copy.deepcopy(data)
        revised_input['context']=data.get('context','')+'\nUser challenges the assessment (consider critically): '+challenge
        revised=call_model(revised_input)
        changes=[]
        for before,after in zip(original['assessment']['turns'],revised['assessment']['turns']):
            if before!=after:
                changes.append({'turn_id':after['turn_id'],'before':before,'after':after,
                    'explanation':after.get('reason') or ' '.join(a['rationale'] for a in after['arguments'])})
        if original['assessment']['conversation_summary']!=revised['assessment']['conversation_summary']:
            changes.append({'field':'conversation_summary',
                'before':original['assessment']['conversation_summary'],
                'after':revised['assessment']['conversation_summary'],
                'explanation':'Summary regenerated in light of the challenge; review both versions.'})
        out={'original':original,'revised':revised,'changes':changes,
             'notice':'Compare complete assessments; changes may include assessability and summary differences. Revision is not assumed more correct.'}
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except ValueError as e:
        print(json.dumps({'error_type':type(e).__name__,'error':str(e)}),file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # No transcript content or model response is written to logs on errors.
        print(json.dumps({'error_type':type(e).__name__,'error':'Assessment failed validation or execution. No partial result accepted. Check input, local server, and tests.'}),file=sys.stderr)
        sys.exit(1)
