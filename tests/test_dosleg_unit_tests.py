from senapy.dosleg.parser import guess_senate_text_url


def test_url_guessing():
    step = {
        "step": "commission",
        "date": "2014-08-12"
    }
    data = {
        "senat_id": "pjl12-XXX",
        "proposal_type": "PJL"
    }
    text = "\nBlablabla texte n° 221\nTexte de la commission n° 328 (2016-2017) déposé le 25 janvier 2017\n\nBla Bla Bla\n"

    url = guess_senate_text_url(text, step, data)
    assert url == "https://www.senat.fr/leg/pjl16-328.html"

    text = "\nTexte de la commission n° 666 (2007-2008)"
    url = guess_senate_text_url(text, step, data)
    assert url == "https://www.senat.fr/leg/pjl07-666.html"

    text = "\nTexte de la commission n° 666"
    url = guess_senate_text_url(text, step, data)
    assert url == "https://www.senat.fr/leg/pjl13-666.html"

    step["step"] = "hemicycle"
    text = "Texte n° 666"
    url = guess_senate_text_url(text, step, data)
    assert url == "https://www.senat.fr/leg/tas13-666.html"
