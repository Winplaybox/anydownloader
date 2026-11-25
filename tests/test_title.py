import unittest
from backend.utils.title import summarize_title, make_download_filename, safe_content_disposition

class TestTitleSummarizer(unittest.TestCase):
    def test_hanuman_chalisa_youtube_audio(self):
        # User's exact screenshot test case:
        title = "संकट दूर करने वाली चालीसा 🙏 Hanuman Chalisa #hanumanchalisa #hanuman #bhakti #bhajan #lyrics"
        short = summarize_title(title)
        self.assertEqual(short, "Hanuman_Chalisa")
        
        filename = make_download_filename(title, "youtube", "320kbps Audio (MP3)", "mp3")
        self.assertEqual(filename, "Hanuman_Chalisa-youtube_320kbps_Audio_MP3.mp3")

        header = safe_content_disposition(filename)
        self.assertIn('filename="Hanuman_Chalisa-youtube_320kbps_Audio_MP3.mp3"', header)
        self.assertIn("filename*=UTF-8''Hanuman_Chalisa-youtube_320kbps_Audio_MP3.mp3", header)

    def test_bracketed_noise_and_emojis(self):
        title = "Coldplay - Viva La Vida (Official Music Video) [4K Remastered] 🎵🔥"
        short = summarize_title(title)
        self.assertEqual(short, "Coldplay_Viva_La_Vida")

        filename = make_download_filename(title, "youtube", "1080p Full HD", "mp4")
        self.assertEqual(filename, "Coldplay_Viva_La_Vida-youtube_1080p_Full_HD.mp4")

    def test_devanagari_pure_unicode(self):
        title = "श्री हनुमान चालीसा | संकटमोचन हनुमान | संकट कटे मिटे सब पीरा"
        short = summarize_title(title)
        self.assertTrue(len(short) > 0)
        self.assertIn("हनुमान", short)

        filename = make_download_filename(title, "youtube", "320kbps", "mp3")
        self.assertTrue(filename.endswith("-youtube_320kbps.mp3"))

        # Header must be Latin-1 safe in filename="..." and UTF-8 in filename*=...
        header = safe_content_disposition(filename)
        # Check that header can be encoded in latin-1 without exception
        header.encode('latin-1')

    def test_empty_or_url_title(self):
        self.assertEqual(summarize_title(""), "")
        self.assertEqual(summarize_title(None), "")
        self.assertEqual(summarize_title("https://www.youtube.com/watch?v=123"), "")

        fn = make_download_filename("", "youtube", "1080p", "mp4")
        self.assertEqual(fn, "youtube_1080p.mp4")

    def test_long_title_truncation(self):
        long_title = "This is an extremely long title for a video that goes on and on and on and contains way too many words"
        short = summarize_title(long_title, max_words=5, max_chars=35)
        words = short.split('_')
        self.assertLessEqual(len(words), 5)
        self.assertLessEqual(len(short), 35)

if __name__ == '__main__':
    unittest.main()
