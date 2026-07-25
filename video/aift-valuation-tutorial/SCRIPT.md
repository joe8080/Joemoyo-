# SCRIPT — Build Your Own Price: The AI Finance Toolkit Valuation Engine

**Runtime target:** 15:00 · **Word count:** ~2,150 · **Pace:** ~145 wpm
**Voice:** measured, plain, sceptical. Teaching a peer, not selling.
**Rule:** every number on screen comes from the live workbook. Nothing invented.

Swept against `banned-ai-language.md`. Contractions throughout. Sentences average
~12 words because this is spoken, not read.

---

## CH0 · COLD OPEN — 0:00–0:50

> [Own Price cell resolving to $2.09 against a $1.25 market price]

This spreadsheet says a stock is worth two dollars nine.

The market says one twenty-five.

That's sixty-seven percent upside, sitting in a cell, looking very confident.

I don't believe it yet. And by the end of this you won't either — not until
you've seen what's holding it up.

Because I opened this model this morning and found a bug that broke the two
cells everything depends on. The upside number. And the verdict.

So this isn't a tour. We're going to build the thing, break it, fix it, and
work out how much of that sixty-seven percent survives.

This is the Own-Price Valuation Engine from the AI Finance Toolkit. It works on
any listed company. Today it's pointed at a small uranium producer called
enCore Energy.

Let's open it up.

---

## CH1 · WHAT THE ENGINE ACTUALLY DOES — 0:50–2:20

> [Three legs animating into a blend, then a haircut]

Here's the whole idea in one line.

You take three separate estimates of what a share is worth. You weight them.
Then you take a haircut for the fact that you can't sell instantly at a fair
price. What comes out is your own price.

Not the analyst's price. Not the market's price. Yours — because you set every
assumption underneath it.

Leg one is a discounted cash flow. What the business generates, discounted back
to today.

Leg two is peers. What the market pays for comparable companies, applied to
this one.

Leg three is the analyst target. Someone else's homework, used as a sanity
check, not gospel.

For enCore those three come out at one twenty-five, three seventeen, and three
seventy-five.

Look at that spread. The low estimate is a third of the high one. That's not a
flaw in the model — that's the honest answer for a company this early. Three
reasonable methods disagree violently.

A model that hid that spread would be lying to you. This one puts it on the
front page.

---

## CH2 · THE INPUTS SHEET, AND THE BUG — 2:20–4:20

> [Inputs sheet, section A. Zoom on B8. #VALUE! cascade lighting up]

Everything starts on the Inputs sheet. Blue cells are yours to edit. Everything
else is calculated.

Section A is the company. Share price. Share count. Cash. Debt.

enCore has forty-one point six million in cash, seventy point one in marketable
securities — that includes a stake in another uranium company — and a hundred
and fifteen million convertible note.

Add those up and net cash is minus three point three million. Slightly negative.
The model uses the note's face value, which is the conservative choice.

Now watch this cell. Share price. One dollar twenty-five.

It looks like a number. It's formatted like a number. It's text.

Someone typed a dollar sign into a cell that was already formatted as currency.
Excel took it literally and stored the whole thing as a string.

And here's the damage.

Market cap multiplies price by shares. Broken. The cap-size classifier reads
market cap. Broken. The peers table pulls that same market cap. Broken.

Then, on the answer sheet — upside, broken. Verdict, broken.

The two cells you actually look at. Gone. And the sheet gives you no warning,
because every other number still calculates perfectly.

The fix takes two seconds. Retype it as one point two five, no dollar sign, and
let the cell's format add the symbol.

I'm showing you this because it's the most common way a model lies quietly. Not
wrong logic. A text cell wearing a number's clothes.

---

## CH3 · THE CAP-SIZE ENGINE — 4:20–5:50

> [Calibration table, bucket thresholds, size premium and DLOM columns]

Once market cap works, this section does something most retail models skip.

It sizes the company, then charges it for being small.

Under three hundred million is micro. Up to two billion is small. Up to ten
billion is mid. Above that, large.

Each bucket carries two penalties.

A size premium, added to the discount rate. Small companies are riskier, so
future cash is worth less today. Micro-cap gets four and a half percent.

And a liquidity discount, taken off the final price. This one's about whether
you can actually get out. Micro-cap default is twenty-five percent.

enCore is micro on market cap. But look — the liquidity discount has been
overridden down to ten percent.

That's a judgement call, and it's the right one. Twenty-five percent comes from
studies of restricted stock you genuinely can't sell. enCore trades on NASDAQ
every day. Charging it a private-company haircut would be wrong.

The model lets you override. It also shows you what you overrode. That's the
part that matters — the default is still sitting there in the cell next door.

---

## CH4 · BUILDING THE DISCOUNT RATE — 5:50–7:20

> [Risk-free → beta × ERP → base cost of equity → + size premium]

The discount rate decides almost everything in a DCF, so it gets built in the
open rather than typed in as one number.

Start with the risk-free rate. US ten-year, four point five five percent.

Add the equity risk premium — what investors want on top for holding stocks at
all. Five percent here.

Multiply that premium by beta. Beta is how violently this thing moves against
the market. One point three, because micro-cap uranium is not a utility.

Four point five five, plus one point three times five, gives eleven point oh
five percent. That's the base cost of equity.

Then add the size premium from the bucket. Four and a half points.

Fifteen point five five percent.

That's a punishing rate, and it should be. At that discount, a dollar arriving
in five years is worth forty-nine cents today. It cuts the terminal value
roughly in half before anything else happens.

If you think that's too harsh, change beta or change the bucket. Just change it
where the whole sheet can see it.

---

## CH5 · THE DCF, AND THE UNCOMFORTABLE PART — 7:20–9:50

> [Five-year build, production → revenue → costs → EBITDA → capex → FCF]

Five years. Twenty-six through thirty.

Production ramps from seven hundred thousand pounds to two and a half million.
Realised price climbs from sixty-eight dollars a pound to eighty-eight, as older
low-priced contracts roll off.

Revenue is those two multiplied. Forty-seven million growing to two hundred and
twenty.

Costs come off per pound. Forty-six dollars falling to forty as scale improves.
Then overhead, seventeen and a half percent of revenue.

That gives EBITDA. Seven million in year one, up to eighty-one and a half by
2030. Genuinely good progress.

Then capex.

Twenty-five, thirty, forty, ninety, ninety.

And free cash flow goes negative. Every single year.

Minus seventeen point nine. Minus fourteen point six. Minus six point five.
Minus thirty-three point four. Minus eight point five.

Add up the present value of five years of operating cash flow and you get minus
fifty-three and a half million.

The operating business, across the entire forecast, subtracts fifty-three
million from the valuation.

So where does a two dollar price come from?

Terminal value. All of it. Every penny of enCore's worth in this model sits
past 2030.

That's not automatically wrong. Mines cost money before they make money. But
you need to say it out loud, because it changes what you're actually betting
on. You're not buying five years of cash flow. You're buying the assumption
that something valuable exists at the end of them.

---

## CH6 · TERMINAL VALUE — TWO METHODS, ONE BIG GAP — 9:50–11:20

> [Gordon growth vs exit multiple, side by side, $350M vs $618M]

Since terminal value is carrying the entire valuation, how you calculate it
stops being a detail.

Method one, Gordon growth. Take normalised cash flow, grow it forever at two
percent, discount it. Three hundred and fifty million.

Method two, exit multiple. The market pays roughly twelve dollars per pound of
resource in the ground. enCore has fifty-one and a half million pounds. Six
hundred and eighteen million.

Same company. Same day. Same sheet. Two hundred and sixty-eight million apart.

The exit multiple is seventy-six percent higher.

This model uses the exit multiple, which is the more generous of the two. And
the toggle for that choice is one dropdown on the Inputs sheet.

Flip it to Gordon growth and watch the own price fall. That's not the model
being unreliable. That's the model showing you honestly how much of your answer
was a method choice rather than a fact about the business.

Any valuation that gives you one number without showing you that gap is hiding
something.

---

## CH7 · PEERS, AND A TRAP WORTH KNOWING — 11:20–12:40

> [Peer table; then the shared-lever link between Inputs!B45 and both legs]

The peer sheet checks the DCF against what the market actually pays.

Cameco, sixty-four and a half billion, producing. NexGen, eleven billion, not
producing anything yet. Uranium Energy, Denison, Energy Fuels, Kazatomprom,
Ur-Energy.

The lesson in this table is that producers get a premium over developers, and
the gap is enormous. NexGen is worth eleven billion with zero pounds coming out
of the ground.

Apply twelve dollars a pound to enCore's resource and you get six hundred and
eighteen million enterprise value. Adjust for cash and debt, divide by shares,
and the peer-implied price is three seventeen.

Now — the trap.

That twelve dollars per pound? It's the same cell that drove the terminal value
in the DCF.

So when the peer leg and the DCF leg agree, they're not confirming each other.
They're both repeating one assumption you made once.

To this model's credit, it flags this itself. There's a note in the cell saying
the lever is shared.

But you should know what it means. If you want the peer check to be a real
second opinion, give it its own dollars-per-pound. Otherwise you've got one
opinion wearing two hats.

---

## CH8 · THE BLEND — 12:40–14:00

> [OwnPrice sheet resolving line by line]

Now the answer sheet, and it's the simplest page in the workbook.

Three prices. One twenty-five from the DCF. Three seventeen from peers. Three
seventy-five from analysts.

Weights: fifty percent DCF, thirty percent peers, twenty percent analysts. They
have to total a hundred, and there's a check cell that tells you off if they
don't.

Weighted, that's two dollars thirty-three.

Then the liquidity haircut. Ten percent off.

Two dollars nine. Against a market price of one twenty-five.

Sixty-seven percent upside. Verdict: undervalued on your assumptions.

Read those last three words again. On your assumptions.

The model isn't claiming enCore is worth two dollars nine. It's saying: if
uranium holds up, if production ramps, if twelve dollars a pound is fair, and
if the terminal year arrives roughly as sketched — then two dollars nine.

Change any one of those and the number moves. That's the honest version of
valuation, and it's why the sheet is built so every assumption has its own cell
with your fingerprints on it.

---

## CH9 · STRESS IT, THEN LOG IT — 14:00–15:00

> [Sensitivity table, then the version log row]

Two sheets left, and they're the ones that turn this from a calculator into a
practice.

The sensitivity table runs uranium from fifty dollars to a hundred and ten.
Costs and production stay pinned to the DCF, so only price moves.

Bear case, six point three million gross profit. Bull case, forty-one point
three. Roughly six and a half times, from a price range that uranium has
genuinely traded through.

That's your real risk. Not the spreadsheet — the commodity.

And then the version log. Every time you run this, it stamps the date, the
bucket, the discount rate, and the price you got, and you paste it in as a
frozen row.

Do that for a year and you can see whether your own prices were any good. Most
people never find out, because they never wrote the number down.

So: fix the text cell. Split the shared lever if you want two real opinions.
Flip the terminal value method and see what survives. And log every run.

The workbook's linked below, bug already fixed. Tell me which company you'd
point it at first.

---

## Numbers used — all traced to the workbook

| Claim | Cell |
|---|---|
| Own Price $2.09 | `OwnPrice!B10` |
| NAV $1.252 | `DCF!B30` |
| Peer $3.165 | `Peers!B20` |
| Analyst $3.75 | `Inputs!B51` |
| Net cash −$3.3M | `Inputs!B16` |
| Discount rate 15.55% | `Inputs!B40` |
| Size premium 4.5% | `Inputs!B22` |
| Liquidity 25% default / 10% used | `Inputs!B23` / `B25` |
| FCF −17.9 … −8.5 | `DCF!B14:F14` |
| Sum PV FCF −$53.5M | `DCF!B25` |
| TV Gordon $350.0M | `DCF!B21` |
| TV Exit $618M | `DCF!B22` |
| Blended $2.326 | `OwnPrice!B8` |
| Bear/Bull gross profit 6.3 / 41.3 | `Sensitivity!I5` / `I8` |

**Bug:** `Inputs!B8` holds the string `"$1.25"` under a `\$0.00` format. Breaks
`Inputs!B12`, `Inputs!B20`, `Peers!C12`, `OwnPrice!B12`, `OwnPrice!B13`.
