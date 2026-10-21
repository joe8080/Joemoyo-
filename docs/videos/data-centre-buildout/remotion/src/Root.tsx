import React from 'react';
import {Composition} from 'remotion';
import {Plate, PLATE_FRAMES} from './Plate';
import {Film, FILM_FRAMES} from './Film';
export const Root: React.FC = () => (
  <>
    <Composition id="Film" component={Film} durationInFrames={FILM_FRAMES} fps={30} width={1920} height={1080} />
    <Root2 />
    <Composition id="Plate" component={Plate} durationInFrames={PLATE_FRAMES} fps={30} width={1280} height={720} />
  </>
);
import {PlateBG, Header, Tracker, Captions, Waveform} from './Overlays';
import {Cold, Q1, Q2} from './Scenes1';
import {FontLoader} from './ui';
const W: React.FC<{children: React.ReactNode}> = ({children}) => <div style={{width: 1920, height: 1080, position: 'relative', overflow: 'hidden', background: '#04060c', color: '#e7ecf6'}}><FontLoader />{children}</div>;
export const Root2: React.FC = () => (
  <>
    <Composition id="PlateOnly" component={() => <W><PlateBG /></W>} durationInFrames={9000} fps={30} width={1920} height={1080} />
    <Composition id="NoPlate" component={() => <W><Cold /><Q1 /><Q2 /><Header /><Tracker /><Captions /></W>} durationInFrames={9000} fps={30} width={1920} height={1080} />
    <Composition id="WaveOnly" component={() => <W><Waveform /></W>} durationInFrames={9000} fps={30} width={1920} height={1080} />
  </>
);
