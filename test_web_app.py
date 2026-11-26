import json
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import web_app
from test_assess import fixture

class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),web_app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def post(self,path,data,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        request=urllib.request.Request(self.url+path,data=json.dumps(data).encode(),headers=headers)
        try:
            with urllib.request.urlopen(request) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)

    def test_home_loads_input_without_calling_model(self):
        with patch('web_app.assess.call_model') as model:
            with urllib.request.urlopen(self.url) as response:
                page=response.read().decode()
                self.assertIn('id="transcript"',page)
                self.assertIn('id="results" class="panel" hidden',page)
                self.assertEqual(response.headers['Cache-Control'],'no-store')
            model.assert_not_called()

    def test_blank_quick_input_does_not_score(self):
        with patch('web_app.assess.quality') as model:
            self.assertEqual(self.post('/api/quality',{'text':'  '})[0],422)
            model.assert_not_called()

    def test_unreviewed_conversation_does_not_call_model(self):
        data,_=fixture();data['reviewed']=False
        with patch('web_app.assess.call_model') as model:
            self.assertEqual(self.post('/api/assess',data)[0],422)
            model.assert_not_called()

    def test_reviewed_submission_calls_model_once(self):
        data,_=fixture()
        with patch('web_app.assess.call_model',return_value={'assessment':'test'}) as model:
            status,result=self.post('/api/assess',data)
            self.assertEqual(status,200);self.assertEqual(result,{'assessment':'test'})
            model.assert_called_once_with(data)

    def test_cross_origin_submission_rejected(self):
        with patch('web_app.assess.quality') as model:
            self.assertEqual(self.post('/api/quality',{'text':'Hello'},'https://example.com')[0],403)
            model.assert_not_called()

    def test_offline_model_has_actionable_error(self):
        data,_=fixture()
        with patch('web_app.assess.call_model',side_effect=urllib.error.URLError('offline')):
            status,result=self.post('/api/assess',data)
            self.assertEqual(status,503);self.assertIn('run.ps1 server',result['error'])

    def test_over_limit_rejected_before_model(self):
        data,_=fixture();data['turns'][0]['text']='x'*4001
        with patch('web_app.assess.call_model') as model:
            self.assertEqual(self.post('/api/assess',data)[0],422);model.assert_not_called()

    def test_challenge_returns_both_versions(self):
        data,assessment=fixture();original=web_app.assess.validate_response(data,assessment)
        with patch('web_app.assess.call_model',return_value=original):
            status,result=self.post('/api/challenge',{'input':data,'original':original,'challenge':'Reconsider the reasoning.'})
            self.assertEqual(status,200);self.assertEqual(result['original'],result['revised'])
            self.assertEqual(result['changes'],[])

    def test_static_path_does_not_expose_files(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(self.url+'/assess.py')
        self.assertEqual(error.exception.code,404)

if __name__=='__main__':unittest.main()
