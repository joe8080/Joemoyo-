# OGX "Adwa, 1896" script v05 (Joe voice pass; maps = real terrain zooms): narration + one planned picture per line.
# Visual specs:
#   ("arch", key, crop or None)   archive image framed, credit strip
#   ("ai", key)                   AI reconstruction, full bleed, labelled
#   ("card", kicker, title)       text card on dark-green ground
#   ("map", name)                 own drawn map
# Each line: (text, visual, on_screen_text_or_None)

VOICE_SUBS = {"Wuchale": "Wuchalé", "Mekelle": "Mekellay"}

ACTS = [
("COLD OPEN", None, [
 ("Have a look at this picture. It was printed in Paris, in the summer of eighteen ninety-eight.", ("arch", "A01", None), "PARIS · 1898"),
 ("That's an African emperor in a red cape, riding through the rocks at a place called Adwa.", ("arch", "A01", (0.08, 0.22, 0.92, 0.88)), None),
 ("Adwa is a town in the mountains of northern Ethiopia, not far from today's border with Eritrea.", ("map", "zoom_adwa"), "ADWA · TIGRAY"),
 ("The artist was never there. But the battle was real.", ("arch", "A01", (0.25, 0.86, 0.75, 0.95)), "IMAGINED IN EUROPE"),
 ("On the first of March, eighteen ninety-six, Ethiopia destroyed an invading Italian army in a single day.", ("ai", "N01"), "1 MARCH 1896"),
 ("If you know this story at all, you probably know how it ends.", ("ai", "N12"), None),
 ("The real question is how they did it.", ("card", "THE QUESTION", "How did Ethiopia win?"), None),
]),
("TITLE", None, [
 ("This is the story of Adwa.", ("title",), None),
]),
("01", "ONE WORD", [
 ("It starts seven years earlier, in eighteen eighty-nine, with a new emperor and a treaty with Italy.", ("arch", "A02", None), "MENELIK II"),
 ("The emperor was Menelik the Second. The treaty was named after the place it was signed: Wuchale.", ("card", "1889", "The Treaty of Wuchale"), None),
 ("Most of it was about friendship, trade and borders. One article wasn't.", ("card", "THE TREATY", "Article 17"), None),
 ("Article seventeen was written in two languages. And here's the problem: the two versions didn't say the same thing.", ("card", "ARTICLE 17", "Two texts"), None),
 ("In the Amharic version, the emperor could use Italy's help in dealing with other powers, if he wanted to.", ("card", "AMHARIC TEXT · PARAPHRASE", "He may"), None),
 ("In the Italian version, he agreed to do so. Read that way, Ethiopia had become an Italian protectorate.", ("card", "ITALIAN TEXT · PARAPHRASE", "He must"), None),
 ("So it comes down to one verb. May, or must.", ("card", "ONE VERB", "May. Must."), None),
 ("Italy told the rest of Europe that it now spoke for Ethiopia. Menelik wouldn't accept that.", ("arch", "A12", None), None),
 ("Historians still argue about whether that was a translator's mistake, or done on purpose. I don't think we can be sure.", ("card", "CONTESTED", "Mistake or design?"), None),
 ("In eighteen ninety-three, Menelik formally rejected the treaty.", ("card", "1889 → 1893", "Treaty renounced"), None),
]),
("02", "THE EMPEROR AND THE EMPRESS", [
 ("To follow what happened next, you need to meet the two people at the centre of the Ethiopian court.", ("ai", "N18"), None),
 ("Menelik had already ruled the kingdom of Shewa for more than twenty years before he became emperor.", ("arch", "A02", (0.05, 0.05, 0.95, 0.75)), "MENELIK II"),
 ("He was patient, and he planned ahead. Through the eighteen-eighties and nineties, he brought in modern rifles in large numbers, many of them from France and Russia.", ("ai", "N21"), None),
 ("Next to him was the empress, Taytu Betul.", ("arch", "A03", None), "TAYTU BETUL"),
 ("And she wasn't just in the background. She was a political force in her own right.", ("arch", "A04", None), None),
 ("Together, in the eighteen-eighties, they founded a new capital and called it Addis Ababa. It means new flower.", ("ai", "N18"), "ADDIS ABABA"),
 ("By one account, it was Taytu who argued hardest against Italy's reading of the treaty, and pressed her husband to stand firm.", ("arch", "A04", (0.15, 0.10, 0.85, 0.70)), "ONE ACCOUNT"),
 ("But there's a harder side to this story too, and it matters.", ("card", "THE OTHER SIDE", "An empire of conquest"), None),
 ("In the same years, Menelik's armies were conquering kingdoms to the south and west, like Wolaita and Kaffa.", ("map", "south"), None),
 ("A lot of those campaigns were brutal. For many people in Ethiopia's south, Menelik is remembered as a conqueror, not a liberator.", ("card", "REMEMBERED DIFFERENTLY", "Conqueror and defender"), None),
 ("Both of those things are true. The empire that fought at Adwa had itself been built by force.", ("ai", "N04"), None),
]),
("03", "THE CALL TO ARMS", [
 ("Over in Rome, the prime minister, Francesco Crispi, wanted an empire. The treaty row gave him his excuse.", ("arch", "A15", None), "FRANCESCO CRISPI"),
 ("Italy already had a colony on the Red Sea coast. It called it Eritrea.", ("map", "region"), None),
 ("In eighteen ninety-five, Italian forces under General Oreste Baratieri pushed south from there, into the Ethiopian province of Tigray.", ("arch", "A05", None), "ORESTE BARATIERI"),
 ("Menelik answered in September.", ("ai", "N03"), None),
 ("He called the whole empire to arms.", ("ai", "N03"), "17 SEPTEMBER 1895"),
 ("And this came after years of famine and cattle disease. Even so, the provinces answered.", ("ai", "N04"), None),
 ("From Shewa and Gojjam, from Tigray and the Oromo lands of Wollo, forces gathered under their own commanders.", ("map", "provinces"), None),
 ("How big was the army? Honestly, nobody knows exactly. Estimates run from about seventy thousand men to more than a hundred thousand.", ("card", "ESTIMATES VARY", "70,000 to 100,000+"), None),
 ("And an army that size has to eat.", ("ai", "N05"), None),
 ("Behind the fighters came pack animals, grain and thousands of camp followers. Just moving all of that north was a huge piece of organisation.", ("ai", "N05"), None),
 ("According to the accounts, Taytu marched with them, at the head of her own troops.", ("arch", "A03", (0.1, 0.05, 0.9, 0.6)), "TAYTU BETUL"),
]),
("04", "FIRST BLOOD", [
 ("The first big clash came on the seventh of December, at a mountain called Amba Alagi.", ("arch", "A09", "amba"), "AMBA ALAGI · 1895"),
 ("Ethiopian forces under Ras Makonnen overran an Italian outpost of around two thousand men. Most of them were Eritrean soldiers.", ("arch", "A09", "amba_tight"), None),
 ("Their commander, Major Pietro Toselli, was killed.", ("card", "7 DECEMBER 1895", "Toselli falls"), None),
 ("The survivors fell back to a fort the Italians had started building at Mekelle.", ("ai", "N06"), "MEKELLE"),
 ("In January, the Ethiopian army surrounded it.", ("ai", "N06"), None),
 ("The fort had one weak spot. Its water was outside the walls.", ("ai", "N07"), None),
 ("So Ethiopian troops took the springs. Some accounts give Taytu the credit for that idea, but the evidence is thinner than the legend.", ("card", "CONTESTED", "Taytu's plan?"), None),
 ("Within about two weeks, the garrison put up a white flag.", ("ai", "N06"), "JANUARY 1896"),
 ("Then Menelik did something you might not expect. He let the Italian soldiers march away.", ("ai", "N08"), None),
 ("Why he did it is still debated. But it was the move of a ruler thinking beyond one battle.", ("arch", "A02", None), None),
]),
("05", "THE STANDOFF", [
 ("By February, the two armies were facing each other in the mountains around Adwa.", ("map", "zoom_tigray"), "ADWA · FEBRUARY 1896"),
 ("Neither commander wanted to attack first across that ground.", ("map", "standoff"), None),
 ("And both armies were running out of food.", ("ai", "N05"), None),
 ("Baratieri thought that if he waited, Menelik's army would have to break up and scatter just to feed itself.", ("arch", "A05", (0.1, 0.12, 0.9, 0.75)), None),
 ("But Rome wasn't going to wait.", ("ai", "N11"), None),
 ("Crispi's telegrams were getting sharper. He wanted a victory.", ("arch", "A15", None), None),
 ("And by most accounts, a general was already on his way from Italy to replace Baratieri.", ("card", "BY MOST ACCOUNTS", "A replacement en route"), None),
 ("On the evening of the twenty-eighth of February, Baratieri called in his brigade commanders and put it to them: pull back, or advance?", ("ai", "N10"), "28 FEBRUARY 1896"),
 ("By most accounts, they told him to advance.", ("ai", "N10"), None),
]),
("06", "THE NIGHT MARCH", [
 ("The plan they came up with was bold.", ("map", "plan_a"), None),
 ("Three brigades would march through the night on separate tracks, and take a line of high ground facing the Ethiopian camp before dawn.", ("map", "plan_b"), None),
 ("On the left was General Matteo Albertone, with a brigade of Eritrean soldiers under Italian officers.", ("ai", "N22"), "ALBERTONE · LEFT"),
 ("General Giuseppe Arimondi had the centre, and General Vittorio Dabormida the right. A fourth brigade followed behind, in reserve.", ("map", "plan_c"), None),
 ("Altogether, somewhere between fifteen and eighteen thousand men.", ("card", "ESTIMATES VARY", "15,000 to 18,000"), None),
 ("They set off at about half past nine at night, on the twenty-ninth of February.", ("ai", "N02"), "29 FEBRUARY 1896"),
 ("It was dark. The tracks were rough. And their maps were poor.", ("ai", "N02"), None),
 ("On paper, it was a plan. In the mountains, it started to fall apart.", ("ai", "N01"), None),
]),
("07", "THE BATTLE", [
 ("Albertone marched further than he was meant to.", ("map", "albertone_a"), None),
 ("By most accounts, his guides told him the hill he'd reached wasn't the one he'd been ordered to hold.", ("map", "albertone_b"), None),
 ("So he kept going, kilometres ahead of the rest of the army.", ("map", "gap"), None),
 ("Soon after half past five in the morning, his brigade ran into the Ethiopian army. On its own.", ("ai", "N12"), "1 MARCH · DAWN"),
 ("His Eritrean soldiers fought hard. But a gap had opened up behind them, and Menelik's commanders poured into it.", ("ai", "N13"), None),
 ("Baratieri ordered Dabormida forward to help.", ("arch", "A05", None), None),
 ("Instead, Dabormida's brigade drifted off to the right, down into a valley, and into a separate fight of its own.", ("map", "dabormida"), None),
 ("Now the Italian army was in pieces.", ("map", "pieces"), None),
 ("Three brigades. Three battles. No line.", ("card", "1 MARCH 1896", "No line"), None),
 ("In the centre, Arimondi's men held on for a while, against charge after charge.", ("ai", "N14"), None),
 ("Then Menelik sent in his reserve.", ("ai", "N13"), None),
 ("According to the accounts, Ras Mikael's Oromo cavalry came down on the Italian flanks.", ("ai", "N15"), "RAS MIKAEL"),
 ("And the centre broke.", ("ai", "N15"), None),
 ("By early afternoon, it was over. Arimondi and Dabormida were dead. Albertone had been taken prisoner.", ("arch", "A07", None), None),
 ("Baratieri was retreating, with whatever was left of his army.", ("ai", "N16"), None),
]),
("08", "THE COST", [
 ("Nobody counted the dead carefully, so the numbers still differ.", ("ai", "N16"), None),
 ("Italy lost about six thousand men killed, and around three thousand were taken prisoner.", ("card", "ITALIAN LOSSES · ESTIMATES", "6,000 dead · 3,000 taken"), None),
 ("A lot of those men were Eritrean soldiers in Italian service. It's worth remembering that Africans died on both sides at Adwa.", ("ai", "N22"), None),
 ("Ethiopian losses were heavy too. Estimates run from about four thousand to seven thousand dead.", ("card", "ETHIOPIAN LOSSES · ESTIMATES", "4,000 to 7,000 dead"), None),
 ("A European army had been beaten in open battle by an African state.", ("arch", "A07", (0.0, 0.0, 0.7, 1.0)), None),
 ("In London, The Graphic printed this scene, drawn from details given by survivors.", ("arch", "A07", None), "THE GRAPHIC · 1896"),
 ("In Italy, people protested in the streets. Within days, Crispi's government had fallen.", ("arch", "A15", None), "ROME · MARCH 1896"),
]),
("09", "THE PEACE", [
 ("Menelik didn't march on to the coast.", ("map", "coast"), None),
 ("He was holding thousands of prisoners, and he used them to bargain.", ("arch", "A09", "prisoners"), None),
 ("In October eighteen ninety-six, the Treaty of Addis Ababa ended the war.", ("card", "OCTOBER 1896", "Treaty of Addis Ababa"), None),
 ("Italy cancelled the Treaty of Wuchale and recognised Ethiopia as a fully independent state.", ("card", "THE TERMS", "Wuchale cancelled"), None),
 ("Within a year, France and Britain had signed their own treaties with Menelik.", ("card", "1897", "France · Britain"), None),
 ("But Italy kept Eritrea. Adwa didn't push Europe out of Africa.", ("map", "africa"), "ERITREA"),
 ("What it did was narrower, but still huge. It kept Ethiopia independent while almost all the rest of the continent was being carved up.", ("ai", "N19"), None),
]),
("10", "WHOSE VICTORY", [
 ("For a long time, Europe told Adwa as a story about Italy.", ("arch", "A13", None), None),
 ("A disaster. A blunder. Generals lost in the dark.", ("arch", "A13", (0.1, 0.1, 0.9, 0.6)), None),
 ("Tell it that way, and the winners almost vanish.", ("card", "THE MISSING HALF", "Who won?"), None),
 ("Ethiopians told it differently.", ("arch", "A10", None), "ETHIOPIAN PAINTING"),
 ("In paintings like this one, made long after the battle, Saint George rides in the sky above the Ethiopian army.", ("arch", "A10", (0.3, 0.0, 0.7, 0.4)), None),
 ("But the victory belongs to the people who planned it, fed it, and fought it.", ("arch", "A10", (0.0, 0.3, 0.6, 1.0)), None),
 ("Far beyond Ethiopia, Black writers and activists, in Africa and across the Atlantic, saw Adwa as proof that colonial rule could be beaten.", ("ai", "N19"), None),
 ("One historian warns that a lot of that meaning was given to Adwa later, by other people. Menelik's own worries were closer to home: his throne, and his state.", ("card", "ONE HISTORIAN", "Meaning made later"), None),
 ("And the independence Adwa protected didn't last forever.", ("ai", "N19"), None),
 ("In nineteen thirty-five, Italy invaded again, under Mussolini, and occupied much of the country until nineteen forty-one.", ("card", "1935 → 1941", "Italy returns"), None),
 ("Today, the first of March is a national holiday in Ethiopia. Adwa Victory Day.", ("ai", "N01"), "ADWA VICTORY DAY"),
]),
("CLOSE", None, [
 ("So, let's go back to that picture printed in Paris.", ("arch", "A01", None), None),
 ("How did Ethiopia win?", ("arch", "A01", (0.08, 0.22, 0.92, 0.88)), None),
 ("Not because of one hero. And not by luck.", ("card", "THE ANSWER", "Not luck"), None),
 ("It won because an emperor armed his state ahead of time, and an empress refused to accept the treaty.", ("arch", "A04", None), None),
 ("Because the provinces answered the call, and the army was fed, moved and led.", ("ai", "N04"), None),
 ("And because the invader marched into the dark, on poor maps, with Rome demanding a victory.", ("ai", "N02"), None),
 ("Ethiopia won at Adwa because it was ready, and Italy wasn't.", ("card", "ADWA · 1896", "Ready"), None),
 ("This has been OrigineX Human Archives.", ("endcard",), None),
 ("Next time, the Valley Tonga, before Lake Kariba. If you think this record is worth keeping, please subscribe.", ("endcard",), None),
]),
]

if __name__ == "__main__":
    import re
    n = sum(len(a[2]) for a in ACTS)
    w = sum(len(re.findall(r"[A-Za-z'-]+", t)) for a in ACTS for t, _, _ in a[2])
    print(f"lines={n} words={w} est_min@145wpm={w/145:.1f}")
    for a in ACTS:
        print(a[0], a[1], len(a[2]), sum(len(t) for t, _, _ in a[2]), "chars")
