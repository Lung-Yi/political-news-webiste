from youtube_transcript_api import YouTubeTranscriptApi

video_id = '182ckTL2KBA'  # 例如：https://www.youtube.com/watch?v=abc123 -> 'abc123'
transcript = YouTubeTranscriptApi.get_transcript(video_id)

for entry in transcript:
    print(f"{entry['start']:.2f}s - {entry['text']}")
