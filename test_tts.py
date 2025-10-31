import openai, os
openai.api_key = os.getenv('OPENAI_API_KEY')
response = openai.audio.speech.create(model='gpt-4o-mini-tts', voice='alloy', input='Test voice, one two three.')
response.stream_to_file('test_voice.mp3')
print('ok')
