import React from 'react';
import {Composition, Still} from 'remotion';
import {Video} from './Video';
import {Thumb} from './nv2';
import TL from './timeline.json';
export const Root: React.FC = () => (
  <>
    <Composition id="Review" component={Video} durationInFrames={TL.total_frames} fps={30} width={1920} height={1080} />
    <Still id="Thumb" component={Thumb} width={1280} height={720} />
  </>
);
