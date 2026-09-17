from backend.app.generation import generate_content_assets

def test_generates_three_reviewable_assets():
    p={'id':1,'name':'Acme Hair','category':'hair salon','city':'Soweto','phone':'0110000000','social_gap':{'state':'OBSERVED'},'evidence':[{'state':'VERIFIED','value':'20 reviews','source_url':'https://example.com'}]}
    r=generate_content_assets(p,[{'title':'Proof reel'}])
    assert len(r)==3
    assert all(x['verification_state']=='VERIFIED' for x in r)
    assert all(x['script'] and x['caption'] for x in r)

def test_unverified_gap_does_not_make_quiet_claim_publishable():
    p={'name':'Acme','category':'plumber','city':'Joburg','social_gap':{'state':'NOT_VERIFIED'}}
    r=generate_content_assets(p,[])
    assert r[2]['verification_state']=='DRAFT'
    assert 'Do not state' in r[2]['notes']
