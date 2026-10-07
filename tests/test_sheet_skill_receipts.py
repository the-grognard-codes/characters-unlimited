"""Sheet rendering distinguishes calculated checks from attribute receipts."""
from copy import deepcopy
import unittest
from characters_unlimited.pdf_export import sheet_skill_rows


class SheetSkillReceiptTests(unittest.TestCase):
    def test_percentile_row_wins_without_losing_unrelated_physical_receipt(self):
        calculated={'id':'gymnastics','kind':'physical','percentage':55,'additional_checks':[{'name':'Balance','percentage':65}]}
        raw={'id':'gymnastics','kind':'physical','additional_checks':[{'name':'Balance','base':60}]}
        building={'id':'body-building','kind':'physical','physical_bonuses':{'PS':2}}
        rows=[calculated,raw,building]
        before=deepcopy(rows)
        self.assertEqual(sheet_skill_rows(rows),[calculated,{**building,'additional_checks':[]}])
        self.assertEqual(rows,before)

    def test_raw_check_never_becomes_a_fabricated_percentage(self):
        row={'id':'gymnastics','kind':'physical','additional_checks':[{'name':'Balance','base':60}]}
        self.assertEqual(sheet_skill_rows([row]),[{**row,'additional_checks':[]}])
        ordinary={'id':'science','percentage':50,'additional_checks':[{'name':'Alternate','percentage':40}]}
        self.assertEqual(sheet_skill_rows([ordinary]),[ordinary])
