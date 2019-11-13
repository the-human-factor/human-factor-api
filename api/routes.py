from flask_restful import Api

import api.resources as resources
import api.admin.resources as admin

api = Api()

api.add_resource(resources.Video, "/api/videos/<string:video_id>")
api.add_resource(resources.CreateVideo, "/api/videos/create")

api.add_resource(resources.ChallengeList, "/api/challenges")
api.add_resource(resources.CreateChallenge, "/api/challenges/create")
api.add_resource(resources.Challenge, "/api/challenges/<string:challenge_id>")

api.add_resource(resources.ResponseList, "/api/responses")
api.add_resource(resources.CreateResponse, "/api/responses/create")
api.add_resource(resources.Response, "/api/responses/<string:response_id>")

api.add_resource(resources.SequenceList, "/api/sequences")
api.add_resource(resources.CreateSequence, "/api/sequences/create")
api.add_resource(resources.Sequence, "/api/sequences/<string:sequence_id>")

api.add_resource(resources.SequenceResponseList, "/api/sequenceresponses")
api.add_resource(
  resources.CreateSequenceResponseInvite, "/api/sequenceresponses/invite"
)
api.add_resource(resources.StartSequenceResponse, "/api/sequenceresponses/start")
api.add_resource(resources.RespondToSequenceResponse, "/api/sequenceresponses/respond")
api.add_resource(
  resources.SequenceResponse, "/api/sequenceresponses/<string:sequence_response_id>"
)

api.add_resource(resources.UserRegister, "/api/auth/register")
api.add_resource(resources.UserLogin, "/api/auth/login")
api.add_resource(resources.UserLogout, "/api/auth/logout")
api.add_resource(resources.UserRefresh, "/api/auth/refresh")
api.add_resource(resources.UserPassword, "/api/auth/password")


api.add_resource(admin.video.VideoEncode, "/api/admin/videos/encode/<string:video_id>")
api.add_resource(admin.video.VideoEncodeAll, "/api/admin/videos/encode")
