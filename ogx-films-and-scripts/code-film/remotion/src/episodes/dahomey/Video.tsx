// Dahomey / Cotonou 1890: scene map. Each script line (S01..S50) has one scene; timing comes from timeline.json.
import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Backdrop, Grain, SceneShell, Captions, Tag} from '../../kit';
import TL from './timeline.json';
import * as A from './scenesA';
import * as B from './scenesB';

const S: Record<string, React.FC<A.P>> = {...(A as any), ...(B as any)};
const FOA = "Foà's plan, published 1895";
const MAPNOTE = `Schematic, not to scale. Place names from ${FOA}; layout simplified for this film.`;
const LOC = 'Locator map: modern coastline and borders (Natural Earth). Not a period map.';
// [evidence tag, source line, chapter chip]
const META: Record<string, [Tag | undefined, string | undefined, string | undefined]> = {
  S01: ['DIAGRAM', LOC, undefined],
  S02: ['PRIMARY ACCOUNT', 'Garrison figure as given in the French account of the battle', 'COTONOU · 3–4 MARCH 1890'],
  S03: ['PRIMARY ACCOUNT', 'Composition of the garrison as given in the French account', 'COTONOU · 3–4 MARCH 1890'],
  S04: ['PRIMARY ACCOUNT', 'From the French account of the night of 3 March', 'COTONOU · 3–4 MARCH 1890'],
  S05: ['DIAGRAM', 'Schematic of the north bastion. Not to scale.', 'COTONOU · 4 MARCH 1890'],
  S06: ['PRIMARY ACCOUNT', 'From the French account of the attack', 'COTONOU · 4 MARCH 1890'],
  S07: ['ACCORDING TO BAYOL', "Governor Jean Bayol's account. One eyewitness disagrees, as the film shows later", 'COTONOU · 4 MARCH 1890'],
  S08: [undefined, undefined, undefined],
  S09: ['ESTIMATE', 'The date the corps was formed is uncertain', 'WHO THEY WERE'],
  S10: ['ESTIMATE', 'Strength in the late 1870s is an estimate', 'WHO THEY WERE'],
  S11: ['CONTEXT', 'Training as described in nineteenth-century accounts', 'WHO THEY WERE'],
  S12: ['CONTEXT', 'No weapon model has been verified for 1890', 'WHO THEY WERE'],
  S13: ['ACCORDING TO BAYOL', "Order of march as Governor Bayol described it", 'WHO THEY WERE'],
  S14: ['DIAGRAM', MAPNOTE, 'THE ATTACK'], S15: ['DIAGRAM', MAPNOTE, 'THE ATTACK'], S16: ['DIAGRAM', MAPNOTE, 'THE ATTACK'],
  S17: ['DISPUTED', 'The sources give different totals for the attacking force', 'THE ATTACK'],
  S18: ['ONE WITNESS', 'Édouard Foà, Le Dahomey (1895)', 'THE ATTACK'],
  S19: ['DISPUTED', 'Bayol and Nicolas against Foà', 'THE ATTACK'],
  S20: ['PRIMARY ACCOUNT', 'From the French accounts of the fight at the stockade', 'THE ATTACK'],
  S21: ['PRIMARY ACCOUNT', 'Quoted in a French account of the battle', 'THE ATTACK'],
  S22: ['DIAGRAM', MAPNOTE, 'THE COUNTER-ATTACK'], S23: ['PRIMARY ACCOUNT', 'From the French account. Diagram only.', 'THE COUNTER-ATTACK'],
  S24: ['DIAGRAM', MAPNOTE, 'THE COUNTER-ATTACK'], S25: ['DIAGRAM', MAPNOTE, 'THE COUNTER-ATTACK'],
  S26: ['PRIMARY ACCOUNT', 'Times as given in the French account; all approximate', 'THE COUNTER-ATTACK'],
  S27: ['PRIMARY ACCOUNT', 'A single primary account: Nicolas, via Ortus. Secondary sources differ.', 'THE COST'],
  S28: ['ONE WITNESS', "Governor Bayol's account", 'THE COST'], S29: ['ONE WITNESS', "Governor Bayol's account", 'THE COST'],
  S30: ['ONE WITNESS', 'Only Bayol names her', 'THE COST'],
  S31: ['ONE SOURCE', 'Reported in one account. ' + LOC, 'THE COST'],
  S32: ['ONE WITNESS', 'Édouard Foà, who was present', 'THE COST'],
  S33: [undefined, undefined, undefined],
  S34: ['ESTIMATE', 'All figures are estimates from different periods', 'THE INSTITUTION'],
  S35: ['CONTEXT', 'Training as described in nineteenth-century accounts', 'THE INSTITUTION'],
  S36: [undefined, undefined, undefined],
  S37: ['LATER IMAGE', 'F. E. Forbes, Dahomey and the Dahomans (1851). British Library.', 'THE PICTURES'],
  S38: ['LATER IMAGE', 'Postcard by F.-E. Fortier, early 1900s', 'THE PICTURES'],
  S39: ['LATER IMAGE', 'French illustrated press, March 1890', 'THE PICTURES'],
  S40: ['CONTEXT', 'Exhibition troupes toured Europe in the 1890s', 'THE PICTURES'],
  S41: ['MUSEUM RECORD', 'musée du quai Branly – Jacques Chirac, inv. 71.1891.22.186; Cousin, Tassi & Yéhouétomé (2022)', 'THE OBJECTS'],
  S42: ['MUSEUM RECORD', 'Human remains are not shown in this film', 'THE OBJECTS'],
  S43: ['CONTEXT', LOC, 'AFTER COTONOU'], S44: ['CONTEXT', 'The 1892 campaign is a separate war', 'AFTER COTONOU'],
  S45: ['CONTEXT', 'Quoted to show the language of the time', 'AFTER COTONOU'], S46: ['CONTEXT', undefined, 'AFTER COTONOU'],
  S47: ['CONTEXT', 'Nawi was recorded as the last known veteran', 'AFTER COTONOU'],
  S48: [undefined, undefined, undefined], S49: [undefined, undefined, undefined], S50: [undefined, undefined, undefined],
};
const OWN_BG = new Set(['S01', 'S02', 'S04', 'S05', 'S06', 'S14', 'S15', 'S16', 'S17', 'S20', 'S22', 'S23', 'S24', 'S25', 'S28', 'S31', 'S43']);
const NO_CAPTIONS = new Set(['S08']);
export const CAPTIONS = true;

export const Video: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0907'}}>
    <Backdrop />
    {TL.scenes.map((s) => { const Comp = S[s.id]; const len = s.end - s.start; const [tag, source, chapter] = META[s.id] || [];
      return (<Sequence key={s.id} from={s.start} durationInFrames={len} name={s.id}>
        <SceneShell len={len} tag={tag} source={source} chapter={chapter} bare={s.id === 'S08' || s.id === 'S50'}>
          {Comp ? <Comp cues={s.cues} len={len} /> : null}
        </SceneShell>
        {CAPTIONS && !NO_CAPTIONS.has(s.id) && <Captions words={s.words as [string, number][]} len={len} />}
      </Sequence>); })}
    <Grain />
  </AbsoluteFill>
);
