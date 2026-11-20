import unittest
from app.finale_v77_v80.multilingual import MultilingualV79,normalize_language,detect_script
class TestV79(unittest.TestCase):
 def test_locale(self):
  self.assertEqual(normalize_language('pt-BR'),'pt');self.assertEqual(normalize_language('Español'),'es')
 def test_invalid(self):
  with self.assertRaises(ValueError): normalize_language('xx')
 def test_explicit_language(self):
  p=MultilingualV79().prepare('Hello','en');self.assertEqual(p.response_language,'en');self.assertIsNone(p.detected_language)
 def test_auto_fallback(self):
  p=MultilingualV79().prepare('Hello','auto');self.assertEqual(p.response_language,'pt');self.assertEqual(p.detection_method,'unavailable')
 def test_script(self):
  self.assertEqual(detect_script('مرحبا'),'ar');self.assertEqual(detect_script('こんにちは'),'ja')
 def test_translation_without_provider(self):
  self.assertEqual(MultilingualV79().translate('olá','pt','en')['error'],'translation_provider_not_configured')
 def test_translation_injected(self):
  result=MultilingualV79(translator=lambda text,src,dst:'hello').translate('olá','pt','en');self.assertEqual(result['text'],'hello');self.assertTrue(result['translated'])
 def test_detector_injected(self):
  self.assertEqual(MultilingualV79(detector=lambda t:'es').prepare('Hola').response_language,'es')
if __name__=='__main__': unittest.main()
