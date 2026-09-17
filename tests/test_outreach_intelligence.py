from backend.app.outreach_intelligence import build_outreach_intelligence


def test_intelligence_uses_observed_gap_and_evidence():
    p = {
        'name':'Test Salon','category':'hair salon','phone':'0111234567','website':'https://example.com',
        'social_gap':{'state':'OBSERVED','headline':'Strong Social Gap detected.','details':'Instagram activity has been absent for 180 days.','signals':[{'label':'Channel','value':'Instagram'}]},
        'channels':[{'platform':'Instagram','url':'https://instagram.com/test'}],
        'evidence':[{'claim':'Business website','value':'Found','source_url':'https://example.com','state':'VERIFIED'}]
    }
    out=build_outreach_intelligence(p)
    assert out['state']=='OBSERVED'
    assert out['evidence_count']==1
    assert '180 days' in out['why_it_matters']
    assert out['content_opportunities']
    assert 'NahaLabs' in out['outreach_message']


def test_intelligence_does_not_claim_unverified_gap():
    out=build_outreach_intelligence({'name':'X','category':'plumber','social_gap':{'state':'NOT_VERIFIED'},'evidence':[]})
    assert out['state']=='NOT_VERIFIED'
    assert 'does not yet verify' in out['why_it_matters']
