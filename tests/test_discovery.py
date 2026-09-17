from backend.app.discovery import extract_contact_details, extract_social_links, maps_search_url


def test_maps_search_url_is_encoded():
    url = maps_search_url("hair salon", "Soweto, Johannesburg")
    assert "google.com/maps/search" in url
    assert "hair+salon" in url


def test_extracts_public_social_links_without_guessing():
    html = '''
    <a href="https://www.instagram.com/example_salon/">Instagram</a>
    <a href="https://www.facebook.com/example.salon">Facebook</a>
    <a href="https://www.linkedin.com/company/example">LinkedIn</a>
    '''
    links = extract_social_links(html)
    assert links["instagram"] == "https://www.instagram.com/example_salon"
    assert links["facebook"] == "https://www.facebook.com/example.salon"
    assert links["linkedin"] == "https://www.linkedin.com/company/example"
    assert "tiktok" not in links


def test_extracts_sa_phone():
    phone, website = extract_contact_details('<p>Call us on 011 123 4567</p><a href="https://example.co.za">Website</a>')
    assert phone == "011 123 4567"
    assert website == "https://example.co.za"
