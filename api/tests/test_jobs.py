import api.jobs as j
import api.models as m

def test_ingest_source_async(log):
  video = m.Video.create(url="test.webm")
  job = j.ingest_video.queue(video.id)
  assert log.has("Video encoding started")
  assert log.has("Video encoding finished")
  assert job.is_finished
  assert video.encoded_at is not None
