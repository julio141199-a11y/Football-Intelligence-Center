#!/usr/bin/env python3
"""Publish verified priority-league club rosters with safe official contact routes."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKED = "2026-08-22"


MARKETS = [
    {
        "country": "Philippines", "continent": "Asia", "league": "Philippines Football League",
        "source": "https://pff.org.ph/table/philppines-football-league-team-standings/",
        "route": "https://pff.org.ph/pff-club-licensing/", "email": "phifootballfederation@gmail.com",
        "licence": "Confirmed in the published PFF domestic club-licensing rules: Head Coach AFC A or recognised equivalent; verify the current-season recognition procedure with PFF before applying.",
        "clubs": ["Manila Digger FC", "One Taguig FC", "Kaya FC-Iloilo", "Dynamic Herb Cebu", "Aguilas-UMak", "Maharlika FC", "Stallion Laguna FC", "Don Bosco Garelli United", "Tuloy FC", "Valenzuela PB-Mendiola", "Philippine Army FC"],
    },
    {
        "country": "Uzbekistan", "continent": "Asia", "league": "Uzbekistan Super League",
        "source": "https://pfl.uz/news?category_id=13", "route": "https://pfl.uz/", "email": "Not Public",
        "licence": "AFC A compatibility is plausible but not proven by the public 2026 domestic regulation reviewed; obtain UFA/PFL written recognition before treating it as eligible.",
        "clubs": ["Andijon", "Bunyodkor", "Buxoro", "Dinamo Samarqand", "Lokomotiv Tashkent", "Mash'al", "Nasaf", "Navbahor", "Neftchi Fergana", "OKMK", "Paxtakor", "Qizilqum", "Qo'qon-1912", "So'g'diyona", "Surxon", "Xorazm"],
    },
    {
        "country": "Cambodia", "continent": "Asia", "league": "Cambodian Premier League",
        "source": "https://www.cpl-cambodia.com/clubs", "route": "https://www.cpl-cambodia.com/clubs", "email": "Not Public",
        "licence": "AFC Challenge League Head Coach minimum is AFC A, but this does not prove every domestic CPL appointment; confirm FFC/CPL recognition for the relevant club and competition.",
        "clubs": ["Angkor Tiger FC", "Boeung Ket FC", "ISI Dangkor Senchey FC", "Kirivong Sok Sen Chey FC", "Life FC Sihanoukville", "Ministry of Interior FA", "Nagaworld FC", "National Defense Ministry FC", "Phnom Penh Crown FC", "Preah Khan Reach Svay Rieng FC", "Visakha FC"],
    },
    {
        "country": "Myanmar", "continent": "Asia", "league": "Myanmar National League 1",
        "source": "https://the-mff.org/2026/04/09/mnl-women-league-meeting-2026-27/", "route": "https://the-mff.org/", "email": "Not Public",
        "licence": "AFC A compatibility is not yet confirmed from a current public domestic rule; request MFF/MNL recognition in writing.",
        "clubs": ["Shan United", "Yangon United", "Dagon Star United", "ISPE FC", "Hanthawady United", "Maha United", "Yadanarbon FC", "Ayeyawady United", "Thitsa Arman FC", "Chinland FC", "Myawady FC", "Yangon City FC"],
    },
    {
        "country": "Hong Kong, China", "continent": "Asia", "league": "Hong Kong Premier League",
        "source": "https://www.hkfa.com/en/news/competitions/21938/detail", "route": "https://www.hkfa.com/en", "email": "Not Public",
        "licence": "Published AFC competition rules support AFC A at the relevant level, but current HKPL domestic Head Coach eligibility and overseas-certificate recognition still require HKFA confirmation.",
        "clubs": ["BC Rangers", "Eastern", "Eastern District", "Hong Kong FC", "Kitchee SC", "Kowloon City", "Kwoon Chung Southern", "Lee Man", "North District", "Tai Po"],
    },
    {
        "country": "Chinese Taipei", "continent": "Asia", "league": "Taiwan Football Premier League",
        "source": "https://www.ctfa.com.tw/tfpl2025", "route": "https://www.ctfa.com.tw/index.php?Itemid=4651&id=5478&option=com_content&view=article", "email": "info@ctfa.com.tw",
        "licence": "Official CTFA domestic rules accept an equivalent or higher international licence through CTFA conversion/recognition; AFC A is therefore a realistic Head Coach route subject to CTFA approval.",
        "clubs": ["Tainan City TSG", "Hang Yuen FC", "Leopard Cat FC", "Taichung Futuro", "Taichung Rock", "Tatung FC", "Taiwan Power Company", "Ming Chuan University"],
    },
    {
        "country": "Singapore", "continent": "Asia", "league": "Singapore Premier League",
        "source": "https://www.fas.org.sg/competition/singapore-premier-league-2/", "route": "https://www.fas.org.sg/", "email": "Not Public",
        "licence": "The current public SPL competition document reviewed does not establish AFC A Head Coach eligibility; FAS recognition and the current club-licensing criterion must be confirmed.",
        "clubs": ["Albirex Niigata FC (S)", "Balestier Khalsa FC", "BG Tampines Rovers FC", "Geylang International FC", "Hougang United FC", "Lion City Sailors FC", "Tanjong Pagar United FC", "Young Lions"],
    },
    {
        "country": "Indonesia", "continent": "Asia", "league": "Indonesia Super League",
        "source": "https://www.ileague.id/", "route": "https://www.ileague.id/", "email": "Not Public",
        "licence": "Current domestic Head Coach licence equivalence was not proven by the official pages reviewed; AFC A holders must obtain PSSI/ILeague confirmation before applying as Head Coach.",
        "clubs": ["Arema FC", "Bali United FC", "Bhayangkara Presisi Lampung FC", "Borneo FC Samarinda", "Dewa United Banten FC", "Garudayaksa FC", "Isenmulang Kalteng FC", "Java United FC", "Madura United FC", "Persebaya Surabaya", "Persib Bandung", "Persija Jakarta", "Persijap Jepara", "Persik Kediri", "Persita", "PSIM Yogyakarta", "PSM Makassar", "PSS Sleman"],
    },
    {
        "country": "Malaysia", "continent": "Asia", "league": "Malaysia Super League",
        "source": "https://www.malaysianfootballleague.com/Content/Post/Watch/6000", "route": "https://www.malaysianfootballleague.com/", "email": "Not Public",
        "licence": "Current MFL domestic Head Coach minimum and foreign AFC A recognition require written MFL/FAM confirmation; AFC competition rules alone are not domestic proof.",
        "clubs": ["Johor Darul Ta'zim", "Kuching City FC", "Selangor FC", "Kuala Lumpur City FC", "Terengganu FC", "Star City FC", "Negeri Sembilan FC", "Penang FC", "Sabah FC", "DPMM FC", "Melaka FC", "Kelantan Red Warrior FC"],
    },
    {
        "country": "Vietnam", "continent": "Asia", "league": "V.League 1",
        "source": "https://vpf.vn/tin-tuc/thong-cao-bao-chi-le-boc-tham-xep-lich-thi-dau-giai-bong-da-vo-dich-quoc-gia-lpbank-2025-26/", "route": "https://vpf.vn/", "email": "Not Public",
        "licence": "The official 2025/26 competition rules refer coaching qualifications to the current VFF professional-football regulations but do not state AFC A equivalence; obtain VFF/VPF confirmation.",
        "clubs": ["Becamex Ho Chi Minh City", "Cong An Ha Noi", "Cong An Ho Chi Minh City", "Dong A Thanh Hoa", "Ha Noi FC", "Hai Phong FC", "Hoang Anh Gia Lai", "Hong Linh Ha Tinh", "Ninh Binh FC", "PVF-CAND", "SHB Da Nang", "Song Lam Nghe An", "Thep Xanh Nam Dinh", "The Cong-Viettel"],
    },
    {
        "country": "China PR", "continent": "Asia", "league": "China League One",
        "source": "https://www.cfl-china.cn/zh/content/league/CL1.html", "route": "https://www.cfl-china.cn/zh/index.html", "email": "Not Public",
        "licence": "No current public CFL rule reviewed confirms that an overseas AFC A holder can register as Head Coach; CFA/CFL recognition is required.",
        "clubs": ["Changchun Yatai", "Dalian K'un City", "Foshan Nanshi", "Guangdong GZ-Power", "Guangxi Hengchen", "Jiangxi Dingnan United", "Meizhou Hakka", "Nanjing City", "Nantong Zhiyun", "Ningbo FC", "Shaanxi Union", "Shenzhen Juniors", "Shijiazhuang Gongfu", "Suzhou Dongwu", "Wuxi Wugo", "Yanbian Longding"],
    },
    {
        "country": "China PR", "continent": "Asia", "league": "China League Two",
        "source": "https://www.cfl-china.cn/zh/content/league/CL2.html", "route": "https://www.cfl-china.cn/zh/index.html", "email": "Not Public",
        "licence": "No current public CFL rule reviewed confirms overseas AFC A recognition for Head Coaches; CFA/CFL approval is required.",
        "clubs": ["Qingdao Red Lions", "Shenzhen 2028", "Chengdu Rongcheng B", "Guizhou Guiyang Athletic", "Nantong Haimen Codion", "Shandong Taishan B", "Changchun Xidu", "Jiangxi Lushan", "Hangzhou Linping Wuyue", "Guangzhou Dandelion", "Guangdong Mingtu", "Xiamen Feilu", "Shanghai Second", "Dalian Kewei", "Dalian Yingbo B", "Hubei Istar"],
    },
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main() -> None:
    contacts_path = ROOT / "contacts.json"
    leagues_path = ROOT / "league_intelligence.json"
    contacts = json.loads(contacts_path.read_text(encoding="utf-8"))
    managed_prefix = "club-priority-"
    contacts = [item for item in contacts if not str(item.get("id", "")).startswith(managed_prefix)]

    managed_contacts = []
    for market in MARKETS:
        for club in market["clubs"]:
            managed_contacts.append({
                "id": f"{managed_prefix}{slug(market['country'])}-{slug(market['league'])}-{slug(club)}",
                "continent": market["continent"],
                "country": market["country"],
                "organization": club,
                "type": "Men's Professional Club",
                "role": "Official league contact route",
                "person": "Not Public",
                "email": market["email"],
                "phone": "Not Public",
                "website": market["route"],
                "facebook": "Not Public",
                "instagram": "Not Public",
                "linkedin": "Not Public",
                "applicationPage": market["route"],
                "priority": "High",
                "source": f"Official {market['league']} participant source",
                "sourceUrl": market["source"],
                "lastChecked": CHECKED,
                "accuracyLevel": "Verified current participant; direct club contact not publicly verified",
                "notes": f"{market['league']}. Use the official league/association route to request the club decision-maker or CV channel. {market['licence']}",
                "dataPolicy": "Public professional route only; no inferred private email or phone.",
            })

    managed_contacts.sort(key=lambda x: (x["country"], x["organization"], x["role"]))
    contacts.extend(managed_contacts)
    contacts_path.write_text(json.dumps(contacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    leagues = json.loads(leagues_path.read_text(encoding="utf-8"))
    by_country = {}
    for market in MARKETS:
        by_country.setdefault(market["country"], []).append(market)
    aliases = {"Taiwan": "Chinese Taipei", "China": "China PR", "Hong Kong": "Hong Kong, China"}
    for item in leagues:
        country = aliases.get(item.get("country"), item.get("country"))
        markets = by_country.get(country)
        if not markets:
            continue
        item["topDivision"] = " / ".join(m["league"] for m in markets)
        item["topDivisionTeams"] = sum(len(m["clubs"]) for m in markets)
        item["headCoachMinimumLicence"] = markets[0]["licence"]
        item["afcAHeadCoachPossibility"] = "Confirmed subject to association recognition" if country in {"Philippines", "Chinese Taipei"} else "Association confirmation required"
        item["officialLeagueWebsite"] = markets[0]["route"]
        item["officialSourceUrls"] = list(dict.fromkeys(m["source"] for m in markets))
        item["lastChecked"] = CHECKED
        item["accuracyLevel"] = "Official league roster verified; licence conclusion limited to published evidence"
        item["notes"] = "Current participant roster and safe official contact route published. Club-direct email/SNS remains Not Public until verified."
    leagues_path.write_text(json.dumps(leagues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Published {sum(len(m['clubs']) for m in MARKETS)} priority club contact routes across {len(MARKETS)} league records.")


if __name__ == "__main__":
    main()
