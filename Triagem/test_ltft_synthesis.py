import unittest
from ltft_synthesis import plan


class SynthesisTests(unittest.TestCase):
    def test_mass_and_purity(self):
        reagents = {'Co':dict(formula='Co(NO3)2',waters=6,purity=100),
                    'Fe':dict(formula='Fe(NO3)3',waters=9,purity=100),
                    'K':dict(formula='KNO3',waters=0,purity=100)}
        table,support = plan('Co0.5Fe0.5','K',100,15,2,reagents)
        self.assertAlmostEqual(table['Massa elementar (g)'].sum()+support,100)
        self.assertGreater(table.iloc[0]['Massa elementar (g)'],table.iloc[1]['Massa elementar (g)'])
        original = table.iloc[0]['Massa a pesar (g)']
        reagents['Co']['purity']=50
        adjusted,_=plan('Co0.5Fe0.5','K',100,15,2,reagents)
        self.assertAlmostEqual(adjusted.iloc[0]['Massa a pesar (g)'],2*original)

    def test_invalid(self):
        with self.assertRaises(ValueError): plan('Co','',100,100,0,{})
        with self.assertRaises(ValueError): plan('Co','',100,10,1,{})
        with self.assertRaises(ValueError): plan('Co','',100,10,0,{'Co':dict(formula='NaCl',waters=0,purity=100)})


if __name__ == '__main__': unittest.main()
