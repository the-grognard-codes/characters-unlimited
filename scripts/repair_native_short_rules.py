"""Restore three short HU2 rules checked in rendered PDF text blocks."""
from repair_source_passages import ROOT, replace_paragraph, save_repairs


def main():
    name="Heroes Unlimited - RPG - 2E.md"
    replace_paragraph(name,"Game Master and players:","Game Master and players: At least two players plus the G.M. An average-sized group of players is 4-6, although 7-12 are not uncommon.",12,11,"Recovered omitted group-size figures from rendered block")
    replace_paragraph(name,"Attribute Bonuses should be added", "Attribute Bonuses should be added to the character's attributes immediately. These are one time bonuses and do not count toward a bonus die roll.",173,172,"Removed corrupted duplicate sentence and recovered rule from rendered block")
    replace_paragraph(name,"In the alternative, the character can create a sort of bubble", "In the alternative, the character can create a sort of bubble that covers a 10 foot diameter (3 m) that will cover light around it and effectively cause lasers and light beams to curve around it, thus protecting those inside the bubble. Other beams of energy, magic, psionics, projectiles and physical force will pass through the light bubble effortlessly. Maximum range this protective bubble can be cast is 100 feet (30.5 m).",230,229,"Recovered unreadable light-bubble protection text; retained the printed wording 'cover light'")
    save_repairs(ROOT/'reports/ocr-review/source-repairs-12.json')


if __name__=='__main__':main()
