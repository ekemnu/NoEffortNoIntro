"""
Test fixtures for scrape() and sort() — distilled from 208k real No-Intro filenames.

One filename per unique (sort branch × tag separator × has_misc_tag) combination.
Synthetic entries are marked and only cover branches that do not appear in the
real dataset at all.

Usage in tests:
    from testcase import SORT_CASES, SCRAPE_CASES

    @pytest.mark.parametrize("filename,expected", SORT_CASES)
    def test_sort(tmp_path, filename, expected):
        rom = make_rom(filename + ".zip", tmp_path)
        rom.tags = rom.scrape()
        assert rom.sort() == expected
"""

# ---------------------------------------------------------------------------
# SORT_CASES  –  (filename_without_extension, expected_sort_result)
# ---------------------------------------------------------------------------
# Each group is labelled with the sort() branch it exercises.

DEBUG_CASES = [
    ("Some Game (DLC)",
     {"unSrted": ['DLC'], 'regionTags': [], 'languageTags': [], 'miscTags': ['DLC']}),
    ]


SORT_CASES = [

    # ── USA region → "USA" ──────────────────────────────────────────────────
    # Region tag fires first; any other regions alongside it are ignored.
    ("16K Letter Writer (USA)",                                         "USA"),  # bare region
    ("BASIC Line Renumbering Program (USA) (v2.3)",                     "USA"),  # + misc tag
    ("Adobe Illustrator 88 (USA, Europe)",                              "USA"),  # comma Europe multi-region
    ("Pokemon - Yellow Version - Special Pikachu Edition (USA,France)", "USA"),  # comma EurWorld multi-region
    ("Adobe Illustrator (v3.2) (USA, Europe) (CGB+SGB Enhanced)",       "USA"),  # plus sep
    ("2 Games in 1 - Power Rangers - Ninja Storm + Power Rangers - Time Force (USA) (En,Fr,De+En)", "USA"),  # plus sep + misc
    ("Hollowknight - Silksong (Japan, USA) (PC Port)",                  "USA"),  # USA priority over Japan

    # ── Japan (no Europe, no EurWor, no World, no USA) → "Japan" ───────────
    ("Atmark Adapter A Atmark Controller Atmark Keyboard - Key Assign Software (Japan)", "Japan"),  # bare
    ("Atmark Controller Key Assign Software (Japan) (v1.03)",           "Japan"),  # + misc
    ("Digimon Tamers - Battle Spirit (Japan, Korea) (En,Ja)",           "Japan"),  # with Asia region, comma
    ("Mingle Magnet (Japan) (En,Ja) (Rev 1)",                           "Japan"),  # + misc
    ("Double Pack - Sonic Battle & Sonic Advance (Japan) (Ja,Fr,De,Es+En)", "Japan"),  # plus sep
    ("Kohakuiro no Yuigon (Japan) (MSX2+)",                             "Japan"),  # plus sep + misc

    # ── Japan + Region + Language (No En) → Japan takes priority ────────────────
    ("Grand Theft Auto (Japan, Europe) (Ja)",                          "Japan"),   # comma-multiregion
    ("Hitman - Absolution (Japan, Europe) (Fr,Ja)",                    "Japan"),   # comma-multiregion
    ("Final Boss of Pendantry, The (Japan, Canada) (Ja,Fr)",           "Japan"),   
    
    # ── Europe (no USA, no Japan) → "Europe" ────────────────────────────────
    ("Alien Invasion (Europe)",                                         "Europe"),  # bare
    ("Alien Invasion (Europe) (Alt)",                                   "Europe"),  # + misc
    ("32 in 1 Game Cartridge (Europe, Australia)",                      "Europe"),  # with Oceania, comma
    ("Backgammon Royale (France) (En,Fr,De) (v2.50) (4 Jan 91)",        "Europe"),  # comma + misc
    ("2 Disney Games - Lilo & Stitch 2 + Peter Pan - Return to Neverland (Sweden) (En,Fr,De,Es+En,Fr,De,Es,It,Nl)", "Europe"),  # plus sep
    ("Foundation's Waste (Europe) (Coverdisk - The One - Issue 22) (Amiga + ST)", "Europe"),  # plus sep + misc
    
    # ── English World Regions → "Europe" ────────────────────────────────
    ("Acheton and Kingdom of Hamil (United Kingdom)",                   "Europe"),  # bare, no lang
    ("Europe with En-GB (Europe) (En-US, En-GB, fr, de)",               "Europe"),  # bare, no lang

    ("Adventure Collection, The (United Kingdom) (Disk 1)",             "Europe"),  # + misc
    ("Dingo Ate My Baby, The (Australia) (En-Au)",                      "Europe"),  # En Region + UnKwn lang
    ("Where the Billionares Go (New Zealand)",                          "Europe"),  # En Region
    ("Islands in the Stream (Japan, United Kingdom)",                   "Europe"),  # Override Japan
    ("Match Three for Me (Japan, Korea, United Kingdom) (EN-Uk)",       "Europe"),  # Override Japan with another


    # ── PAL tag (no other dominant region) → "Europe" ───────────────────────
    # PAL is treated as a European variant.
    ("Bobby Is Going Home (Brazil) (En) (PAL) (Unl)",                  "Europe"),  # PAL alongside Brazil

    # ── Europe, no En → "World" ─────────────────────────────────────
    ("3D Game Collection - 55-in-1 (Europe) (De)",                      "World"),  # non-En langs

    # ── Japan + Europe (No Langauge or with En) → Europe takes priority ────────────────
    ("Red Dead Redemption 2 (Japan, Europe)",                          "Europe"),  # comma-multiregion
    ("Legend of Zelda - Tears of the Kingdom (Japan, Europe) (En,Ja)", "Europe"),  # comma sep
    ("King's Valley (Japan, Europe) (En)",                             "Europe"),  # no misc
    ("Gradius 2 (Japan, Europe) (En) (Wii U Virtual Console)",         "Europe"),  # + misc

    # ── EurWor country + En → "Europe" ──────────────────────────────────────
    # EurWor = named European country that is not "Europe" itself.
    ("Boxen (Germany) (En)",                                            "Europe"),  # bare, no sep
    ("Albertville 92 (France) (En) (3 inch)",                           "Europe"),  # + misc
    ("My Golf (France) (En,De)",                                        "Europe"),  # comma sep
    ("Adam Wolfe (Austria) (En,Fr,De,Es,It,Nl,Pt,Zh,Ko,Ru,Sr) (1.37.0) (COMPUTER BILD SPIELE 9-2019)", "Europe"),  # comma + misc
    ("2 Games in 1 - Disney Princesas + El Rey Leon (Spain) (Es+En,Fr,De,Es,It,Nl,Sv,Da)", "Europe"),  # plus sep

    # ── EurWor country, no En → "World" ─────────────────────────────────────
    ("3D Game Collection - 55-in-1 (Germany) (Fr,De)",                  "World"),  # comma, non-En langs
    ("Chocks Away (Russia) (Disk 1, Game Disk)",                        "World"),  # comma + misc
    ("2 Games in 1 - Alla Ricerca di Nemo + Gli Incredibili - Una 'Normale' Famiglia di Supereroi (Italy) (Es,It+It)", "World"),  # plus sep
    
    # ── World → "USA" ──────────────────────────────────────────────────
    ("Felix the Cat (World)",                                           "USA"),  # bare
    ("ArduChess (World)",                                               "USA"),  # no tags at all
    ("Gilligan's Gold (World) (Steam)",                                 "USA"),  # misc only
    ("5 Days a Stranger (World) (De,It,Fi,Tr,Hu)",                      "World"),  # non-En/Ja langs
    ("The Sagara Family (World) (Windows, Mac, Linux) (Remastered)",    "USA"),  # misc + no lang
    ("Potential Taper - Rewoke World 03 (World) (En) (WonderWitch) (Unl)", "USA"),  #En + misc
    ("Fever Pitch Soccer (World) (En,Fr,De,Es,It)",                     "USA"),  # comma, En among others
    ("Clowns (World) (En,Ja) (v02) (MAX)",                              "USA"),  # comma + misc
    ("The Best of Both (Japan, World) (En,Ja) (v1701d) (TNG)",          "USA"),  # comma + misc

    # ── World + Ja (no En) → "Japan" ────────────────────────────────────────
    ("Dress Wizard (World) (Ja)",                                       "Japan"),  # bare
    ("15 Game (World) (Ja) (WonderWitch) (Unl)",                        "Japan"),  # + misc
    ("Ninja Jajamaru-kun (World) (Ja) (Virtual Console, Switch Online)","Japan"),  # comma + misc

    # ── Language-only En (no region tag at all) → "USA" ─────────────────────
    # Rare edge case; no real example found in 208k lines, so this is synthetic.
    # SYNTHETIC — not present in the No-Intro dataset:
    ("No Region Game (En)",                                             "USA"),

    # ── Language-only Ja (no region) → "Japan" ──────────────────────────────
    # SYNTHETIC — not present in the No-Intro dataset:
    ("No Region Game (Ja)",                                             "Japan"),

    # ── Language-only, neither En nor Ja (no region) → "World" ─────────────
    # SYNTHETIC — not present in the No-Intro dataset:
    ("No Region Game (De)",                                             "World"),

    # ── No tags at all → "UnKwn" ────────────────────────────────────────────
    # Tricky: the scrape() result has all-empty lists.
    ("Game With Absolutely No Tags",                                    "UnKwn"),

]


# ---------------------------------------------------------------------------
# SCRAPE_CASES  –  (filename_without_extension, expected_partial_tags)
# ---------------------------------------------------------------------------
# Each entry checks that specific keys appear (or are empty) in the
# dict returned by scrape().  Use subset assertions:
#
#   tags = rom.scrape()
#   for k, v in expected.items():
#       assert set(v).issubset(set(tags[k]))
#
# "regionTags', 'languageTags', 'miscTags', 'unSrted" are the dict keys.

SCRAPE_CASES = [
    # {'unSrted': ['USA'], 'regionTags': ['USA'], 'languageTags': [], 'miscTags': []}
    # ── Basic region extraction ──────────────────────────────────────────────
    ("Alien Invasion (Europe)",
     {"unSrted": ['Europe'], 'regionTags': ['Europe'], 'languageTags': [], 'miscTags': []}),

    ("16K Letter Writer (USA)",
     {"unSrted": ['USA'], 'regionTags': ['USA'], 'languageTags': [], 'miscTags': []}),

    ("Atmark Controller Key Assign Software (Japan) (v1.03)",
     {"unSrted": ['Japan', 'v1.03'], 'regionTags': ['Japan'], 'languageTags': [], 'miscTags': ['v1.03']}),

    # ── Multi-region, comma-separated ───────────────────────────────────────
    ("Adobe Illustrator 88 (USA, Europe)",
     {"unSrted": ['USA, Europe'], 'regionTags': ['USA', 'Europe'], 'languageTags': [], 'miscTags': []}),

    ("I Got Three on It (Japan, Europe, Germany) (En)",
     {"unSrted": ['Japan, Europe, Germany', 'En'], 'regionTags': ['Japan', 'Europe', 'Germany'], 'languageTags': ['En'], 'miscTags': []}),

    ("King's Valley (Japan, Europe) (En)",
     {"unSrted": ['Japan, Europe', 'En'], 'regionTags': ['Japan', 'Europe'], 'languageTags': ['En'], 'miscTags': []}),

    # ── Language tags — comma-separated ─────────────────────────────────────
    ("My Golf (Germany) (En,De)",
     {"unSrted": ['Germany', 'En,De'], 'regionTags': ['Germany'], 'languageTags': ['En', 'De'], 'miscTags': []}),

    ("Fantastic Dizzy (Europe) (En,Ja,Fr,De,Es,It)",
     {"unSrted": ['Europe', 'En,Ja,Fr,De,Es,It'], 'regionTags': ['Europe'], 'languageTags': ['En', 'Ja', 'Fr', 'De', 'Es', 'It'], 'miscTags': []}),

    # ── Language tags — plus-separated ──────────────────────────────────────
    ("2 Games in 1 - Disney Princesas + El Rey Leon (Spain) (Es+En,Fr,De,Es,It,Nl,Sv,Da)",
     {"unSrted": ['Spain', 'Es+En,Fr,De,Es,It,Nl,Sv,Da'], 'regionTags': ['Spain'], 'languageTags': ['Es', 'En', 'Fr', 'De', 'It', 'Nl', 'Sv', 'Da'], 'miscTags': []}),

    # ── Misc tags (not region, not language) ────────────────────────────────
    ("Alien Invasion (Europe) (Alt)",
     {"unSrted": ['Europe', 'Alt'], 'regionTags': ['Europe'], 'languageTags': [], 'miscTags': ['Alt']}),

    ("Gradius 2 (Japan, Europe) (En) (Wii U Virtual Console)",
     {"unSrted": ['Japan, Europe', 'En', 'Wii U Virtual Console'], 'regionTags': ['Japan', 'Europe'], 'languageTags': ['En'], 'miscTags': ['Wii U Virtual Console']}),

    # ── PAL tag ─────────────────────────────────────────────────────────────
    ("Bobby Is Going Home (Brazil) (En) (PAL) (Unl)",
     {"unSrted": ['Brazil', 'En', 'PAL', 'Unl'], 'regionTags': ['Brazil', 'PAL'], 'languageTags': ['En'], 'miscTags': ['Unl']}),

    # ── PAL variant tag ─────────────────────────────────────────────────────
    # SYNTHETIC — PAL-A/B variants do not appear as standalone region in dataset:
    ("Some Game (PAL-A)",
     {"unSrted": ['PAL-A'], 'regionTags': ['PAL'], 'languageTags': [], 'miscTags': []}),

    # ── No tags at all ──────────────────────────────────────────────────────
    ("Game With Absolutely No Tags",
     {"unSrted": [], 'regionTags': [], 'languageTags': [], 'miscTags': []}),

    # ── World region ─────────────────────────────────────────────────────────
    ("Felix the Cat (World) (En)",
     {"unSrted": ['World', 'En'], 'regionTags': ['World'], 'languageTags': ['En'], 'miscTags': []}),

    ("5 Days a Stranger (World) (De,It,Fi,Tr,Hu)",
     {"unSrted": ['World', 'De,It,Fi,Tr,Hu'], 'regionTags': ['World'], 'languageTags': ['De', 'It', 'Fi', 'Tr', 'Hu'], 'miscTags': []}),

    # ── Language-only (no region) — synthetic ───────────────────────────────
    ("No Region Game (En)",
     {"unSrted": ['En'], 'regionTags': [], 'languageTags': ['En'], 'miscTags': []}),

     ("Not Even a Real Language (Kl)",
     {"unSrted": ['Kl'], 'regionTags': [], 'languageTags': [], 'miscTags': ['Kl']}),

    ("No Region Game (Ja)",
     {"unSrted": ['Ja'], 'regionTags': [], 'languageTags': ['Ja'], 'miscTags': []}),

    ("No Region Game (En+It)",
     {"unSrted": ['En+It'], 'regionTags': [], 'languageTags': ['En', 'It'], 'miscTags': []}),

    ("No Region Game (En+ It)",
     {"unSrted": ['En+ It'], 'regionTags': [], 'languageTags': ['En', 'It'], 'miscTags': []}),

    # ── Locale-suffix language codes (e.g. Zh-Hant, Fr-CA, En-US) ───────────
    ("2375180 - Saimin Arbeit (World) (En,Zh-Hant,Zh-Hans) (Windows)",
     {"unSrted": ['World', 'En,Zh-Hant,Zh-Hans', 'Windows'], 'regionTags': ['World'], 'languageTags': ['En', 'Zh-Hant', 'Zh-Hans'], 'miscTags': ['Windows']}),

    ("Power Quest (USA) (En-US,En-GB,Fr,De,Es,It) (SGB Enhanced) (GB Compatible)",
     {"unSrted": ['USA', 'En-US,En-GB,Fr,De,Es,It', 'SGB Enhanced', 'GB Compatible'], 'regionTags': ['USA'], 'languageTags': ['En-US', 'En-GB', 'Fr', 'De', 'Es', 'It'], 'miscTags': ['SGB Enhanced', 'GB Compatible']}),

    # ── BIOS entries (common edge case) ─────────────────────────────────────
    ("[BIOS] WonderSwan Boot ROM (Japan) (En)",
     {"unSrted": ['Japan', 'En'], 'regionTags': ['Japan'], 'languageTags': ['En'], 'miscTags': []}),

    ("[BIOS] Nintendo 64 - PIF (Japan, USA)",
     {"unSrted": ['Japan, USA'], 'regionTags': ['Japan', 'USA'], 'languageTags': [], 'miscTags': []}),

    # ── Ampersand in title (HTML-escaped in some sets) ───────────────────────
    ("Tom and Jerry - The Movie (USA, Europe) (En,Ja)",
     {"unSrted": ['USA, Europe', 'En,Ja'], 'regionTags': ['USA', 'Europe'], 'languageTags': ['En', 'Ja'], 'miscTags': []}),

]
