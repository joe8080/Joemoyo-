import React from 'react';
import {FontLoader, A, useT, pr} from './ui';
import {PlateBG, Header, Tracker, Captions, Waveform} from './Overlays';
import {Cold, Q1, Q2} from './Scenes1';
import {Q3, Q4} from './Scenes2';
import {Q5, MapScene, SoWhat, Close} from './Scenes3';

export const FILM_FRAMES = Math.ceil(A.end * 30) + 2;
const Fade: React.FC = () => {
  const {t} = useT();
  const o = Math.max(1 - pr(t, 0, 0.45), pr(t, A.end - 0.2, 0.9));
  return <div style={{position: 'absolute', inset: 0, background: '#04060c', opacity: o, pointerEvents: 'none'}} />;
};
export const Film: React.FC = () => (
  <div style={{width: 1920, height: 1080, position: 'relative', overflow: 'hidden', background: '#04060c', color: '#e7ecf6', fontFamily: "'Atkinson Hyperlegible', sans-serif"}}>
    <FontLoader />
    <PlateBG />
    <Cold /><Q1 /><Q2 /><Q3 /><Q4 /><Q5 /><MapScene /><SoWhat /><Close />
    <Header /><Tracker />
    <Waveform />
    <Captions />
    <Fade />
  </div>
);
