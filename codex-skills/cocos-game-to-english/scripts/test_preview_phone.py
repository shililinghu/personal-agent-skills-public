"""HTTP integration checks for user phone preview versus internal raw QA."""
import importlib.util,tempfile,threading,unittest,subprocess,sys
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('preview',HERE/'serve_preview.py');preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)
class PhonePreview(unittest.TestCase):
 def check_server(self,phone):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder);original=b'<html><canvas id="GameCanvas"></canvas></html>';asset=b'\x00\x01original-asset';(root/'index.html').write_bytes(original);(root/'game.bin').write_bytes(asset)
   server=ThreadingHTTPServer(('127.0.0.1',0),partial(preview.Handler,directory=folder,phone_size=phone));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
   try:
    body=urlopen(base+'/').read()
    if phone:self.assertIn(b'fixed-phone-v1',body);self.assertIn(b'<iframe',body)
    else:self.assertEqual(body,original)
    self.assertEqual(urlopen(base+'/index.html?__phone_game=1').read(),original)
    self.assertEqual(urlopen(base+'/game.bin').read(),asset)
    self.assertEqual((root/'index.html').read_bytes(),original)
   finally:server.shutdown();thread.join();server.server_close()
 def test_default_phone_keeps_actual_game_and_assets(self):self.check_server((390,844))
 def test_internal_raw_keeps_top_level_canvas(self):self.check_server(None)
 def test_raw_cannot_be_user_keep(self):
  with tempfile.TemporaryDirectory()as d:
   (Path(d)/'index.html').write_text('<html>game</html>');r=subprocess.run([sys.executable,str(HERE/'serve_preview.py'),'--directory',d,'--raw','--keep'],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertIn('internal QA',r.stderr)
if __name__=='__main__':unittest.main()
