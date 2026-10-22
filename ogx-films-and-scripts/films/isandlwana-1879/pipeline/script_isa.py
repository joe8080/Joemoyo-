# OGX "Isandlwana, 1879" script v1.0 (from pre-production v0.1; cold open rebuilt on The Graphic, 15 March 1879,
# because no public-domain 1879 battlefield photograph was found). One picture per line; V2 = second picture.
# VOICE_SUBS are spellings for the voice engine only (pronunciation list s.4 of the pre-production pack).
VOICE_SUBS = {
    'Isandlwana': 'Ee-sand-lwana', 'Cetshwayo': 'Ketshwayo', 'OrigineX': 'Origin-ex',
    'Ntshingwayo kaMahole': 'Ntshing-wah-yo, ka-Mah-ho-leh', 'Mavumengwana kaNdlela': 'Mavu-meng-gwana, ka-Ndlela',
    'Ngwebeni': 'Ngweh-beh-ni', 'amabutho': 'ama-boo-to', 'Mkhosana kaMvundlana': 'Mkho-sana, ka-Mvun-dlana',
    'isiqu': 'ee-see-koo', 'Pulleine': 'Pul-een', 'Ulundi': 'Oo-loon-dee',
}

ACTS = [('COLD OPEN', None, [
    ('Have a look at this picture. It was printed in a London newspaper in March, eighteen seventy-nine.',
     ('arch', 'I01', None), 'THE GRAPHIC · LONDON · 1879'),
    ("Two British officers are riding for their lives. One is clutching his regiment's colours.",
     ('arch', 'I01', (0.22, 0.08, 0.92, 0.62)), None),
    ("The artist wasn't there. But the battle behind it was real.", ('arch', 'I01', (0.0, 0.0, 0.62, 0.5)), 'DRAWN IN LONDON'),
    ("On the twenty-second of January, eighteen seventy-nine, a Zulu army destroyed a British camp here, beneath a hill called Isandlwana.",
     ('map', 'zoom_isa'), '22 JANUARY 1879'),
    ('More than thirteen hundred men on the British side were killed in a single afternoon.', ('ai', 'Z01'), None),
    ('The usual story is about what went wrong for the British.', ('arch', 'I06', None), 'A VICTORIAN PAINTING'),
    ("But that's only half of it. The real question is how the Zulu army did it.",
     ('card', 'THE QUESTION', 'How did the Zulu army win?'), None),
    ('And the answer starts with the army itself.', ('ai', 'Z03'), None)]),
 ('TITLE', None, [('This is the story of Isandlwana.', ('title',), None)]),
 ('01', 'AN ULTIMATUM', [
    ("In December eighteen seventy-eight, Britain's High Commissioner, Sir Bartle Frere, sent the Zulu king an ultimatum.",
     ('arch', 'I03', None), 'SIR BARTLE FRERE'),
    ('The king was Cetshwayo. He was told, among other things, to break up the Zulu military system.',
     ('arch', 'I02', None), 'CETSHWAYO kaMPANDE'),
    ('No king could agree to that.', ('arch', 'I02', (0.1, 0.05, 0.9, 0.6)), None),
    ("London hadn't approved a war. Frere went ahead anyway.", ('ai', 'Z31'), None),
    ("In January, British columns crossed into Zululand. One, under Lord Chelmsford, crossed at Rorke's Drift.",
     ('map', 'columns'), 'JANUARY 1879')]),
 ('02', 'AN ARMY OF THE NATION', [
    ('Now, to understand what happened next, you need to understand the army Chelmsford was walking towards.',
     ('ai', 'Z06'), None),
    ('Zulu men were organised into regiments by age, called amabutho. When the king called, they came.',
     ('ai', 'Z03'), 'AMABUTHO · AGE REGIMENTS'),
    ('Most fought with a short stabbing spear and a cowhide shield. Many carried guns too, but mostly old ones, with poor powder.',
     ('ai', 'Z04'), None),
    ('What they had was speed, discipline, and a plan of attack every warrior knew.', ('ai', 'Z05'), None),
    ('They called it the horns of the buffalo.', ('map', 'horns_doctrine'), 'THE HORNS OF THE BUFFALO'),
    ('The chest pins the enemy in front. The horns run wide and close round the sides. The loins wait behind, in reserve.',
     ('map', 'horns_doctrine2'), None),
    ("In the middle of January, the army set out from the king's homestead. Estimates run from about twenty to twenty-five thousand men.",
     ('ai', 'Z06'), 'ESTIMATES · 20,000–25,000'),
    ('It was led by an experienced commander, Ntshingwayo kaMahole, with Mavumengwana kaNdlela.',
     ('ai', 'Z07'), 'NTSHINGWAYO kaMAHOLE')]),
 ('03', 'THE ARMY NOBODY SAW', [
    ('Chelmsford pitched his camp at the foot of Isandlwana.', ('arch', 'I08', None), 'ISANDLWANA TODAY'),
    ("He was expecting to find the Zulu army. He just didn't know where it was.", ('ai', 'Z09'), None),
    ('The Zulu commanders moved their regiments across country in small groups, and brought them together in a valley called Ngwebeni.',
     ('ai', 'Z10'), None),
    ('It was just a few miles from the British camp. Tens of thousands of men. And nobody in the camp knew they were there.',
     ('map', 'ngwebeni'), 'A FEW MILES APART'),
    ('Before dawn on the twenty-second, Chelmsford got reports of Zulu forces to the south-east.', ('ai', 'Z12'), None),
    ('He took a large part of his force out of camp to go after them.', ('map', 'split'), None),
    ('About eighteen hundred men stayed behind, under Lieutenant-Colonel Henry Pulleine. Mid-morning, Colonel Anthony Durnford arrived with more troops.',
     ('ai', 'Z08'), 'ABOUT 1,800 IN AND NEAR THE CAMP'),
    ("Several Zulu accounts say they weren't planning to fight that day, because of the moon. Historians still debate how far the attack was planned.",
     ('ai', 'Z14'), 'SEVERAL ZULU ACCOUNTS · DEBATED')]),
 ('04', 'FOUND', [
    ('Around midday, a patrol of British horsemen rode up onto the high ground and looked down into the Ngwebeni valley.',
     ('ai', 'Z15'), 'AROUND MIDDAY'),
    ('The whole Zulu army was there.', ('ai', 'Z11'), None),
    ("The regiments didn't wait for orders. They rose and came on.", ('ai', 'Z16'), None),
    ('Over the hills, across a front of several miles, the horns of the buffalo began to open.', ('map', 'horns_open'), None)]),
 ('05', 'THE HORNS CLOSE', [
    ('In front of the camp, the British infantry formed a long firing line.', ('ai', 'Z18'), None),
    ('For a while, it held. Rifle and artillery fire stopped the chest at a distance. Warriors went to ground.',
     ('ai', 'Z19'), None),
    ('Then, by Zulu accounts, an induna named Mkhosana kaMvundlana stood up in the open and shamed his men for lying down.',
     ('ai', 'Z20'), 'BY ZULU ACCOUNTS'),
    ('He was shot dead. But the regiment rose, and the charge went in.', ('ai', 'Z21'), None),
    ('Meanwhile the left horn was working round one side of the camp.', ('map', 'left_horn'), None),
    ('And the right horn had gone wide, behind the hill itself, out of sight.', ('map', 'right_horn'), None),
    ("It came down onto the track back to Rorke's Drift, the camp's road home, and closed it.", ('map', 'closed'), 'THE ROAD HOME CUT'),
    ('The British line began to pull back. And as it did, it broke.', ('ai', 'Z22'), None),
    ('In the early afternoon, the camp was overrun. The fighting went on, through the tents and wagons, and along every path out.',
     ('ai', 'Z24'), 'EARLY AFTERNOON'),
    ('That afternoon a partial eclipse dimmed the sun, but by then, the battle for the camp had already been decided.',
     ('ai', 'Z25'), 'PARTIAL ECLIPSE · AFTER THE CAMP FELL')]),
 ('06', 'THE COST', [
    ('More than thirteen hundred men on the British side were killed. Several hundred of them were African soldiers, fighting for the British.',
     ('arch', 'I09', None), 'CAIRNS ON THE FIELD TODAY'),
    ('The Zulu army paid heavily too. Nobody made a full count. Estimates run from about one thousand to more than three thousand dead.',
     ('ai', 'Z26'), 'ZULU DEAD · ESTIMATES 1,000–3,000+'),
    ('Most of what we know comes from British records. Zulu accounts were often collected later, through interpreters, by British interviewers.',
     ('arch', 'I04', None), 'A BRITISH SKETCH · 1879'),
    ("So some of this story we only hear second-hand. But the outcome isn't in doubt.", ('ai', 'Z35'), None)]),
 ('07', 'A BATTLE, NOT A WAR', [
    ("That same afternoon and night, part of the reserve attacked the small post at Rorke's Drift, by most accounts against the king's wishes. About a hundred and fifty men held it.",
     ('ai', 'Z27'), "RORKE'S DRIFT · 22–23 JANUARY"),
    ('And Britain did what an empire could do. It sent more men.', ('ai', 'Z28'), None),
    ('On the fourth of July, eighteen seventy-nine, at Ulundi, the Zulu army was defeated, and the royal homestead burned.',
     ('map', 'ulundi'), 'ULUNDI · 4 JULY 1879'),
    ('In August, Cetshwayo was captured and sent into exile. Zululand was divided into thirteen chiefdoms.',
     ('arch', 'I10', None), 'CETSHWAYO · CAPTURED AUGUST 1879'),
    ('So the Zulu won the battle. But the kingdom lost the war.', ('ai', 'Z02'), None)]),
 ('CLOSE', None, [
    ('In January nineteen ninety-nine, a memorial was unveiled on the battlefield. It is a bronze isiqu, a necklace of valour.',
     ('arch', 'I07', None), 'ZULU MEMORIAL · 1999'),
    ('So, how did the Zulu army win at Isandlwana?', ('arch', 'I01', None), None),
    ('Not by luck. And not just because of British mistakes.', ('ai', 'Z05'), 'THE ANSWER'),
    ('It won because a nation could put a trained army in the field, move it unseen, and attack in a way every man understood.',
     ('ai', 'Z10'), None),
    ('Because its commanders used the ground. And because, when the charge stalled, its regiments got up and went on.',
     ('ai', 'Z21'), None),
    ('And it won because the British camp it found was split, spread out, and too sure of itself.', ('map', 'closed'), None),
    ('This has been OrigineX Human Archives.', ('endcard',), None),
    ('If you think this record is worth keeping, please subscribe.', ('endcard',), None)])]

# second pictures on long lines, keyed by shot number (1-based, title counts as a shot)
V2 = {21: ('ai', 'Z32'), 26: ('ai', 'Z33'), 29: ('ai', 'Z13'), 43: ('ai', 'Z23'), 47: ('ai', 'Z30'), 49: ('ai', 'Z34'),
      51: ('ai', 'Z29')}

def all_lines():
    return [l for a in ACTS for l in a[2]]

if __name__ == "__main__":
    L = all_lines()
    words = sum(len(t.split()) for t, _, _ in L)
    print(len(L), "lines", words, "words")
    for i, (t, v, o) in enumerate(L, 1):
        print(i, v[:2], t[:70])
