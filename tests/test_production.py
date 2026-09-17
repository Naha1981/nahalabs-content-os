from backend.app.production import build_production_brief

def test_build_ugc_brief():
    brief=build_production_brief({'id':7,'type':'REEL_SCRIPT','title':'Show the proof','hook':'Start with the result','script':'Show the work','cta':'Message us','verification_state':'VERIFIED'}, {'id':2,'name':'Acme Salon','category':'hair salon'}, 'INSTAGRAM_REELS')
    assert brief['production_type']=='UGC_VIDEO'
    assert brief['aspect_ratio']=='9:16'
    assert brief['source_content_asset_id']==7
    assert len(brief['shot_list'])==4

def test_non_reel_social_brief():
    brief=build_production_brief({'id':8,'type':'FAQ_POST','title':'FAQ','hook':'Question','script':'Answer','cta':'DM','verification_state':'DRAFT'}, {'name':'Cafe','category':'cafe'}, 'FACEBOOK')
    assert brief['production_type']=='SOCIAL_POST'
    assert brief['aspect_ratio']=='1:1'
