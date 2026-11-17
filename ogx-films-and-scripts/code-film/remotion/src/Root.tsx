import React from 'react';
import {Composition} from 'remotion';
import {Video as Dahomey} from './episodes/dahomey/Video';
import TL from './episodes/dahomey/timeline.json';
export const Root: React.FC = () => <Composition id="dahomey" component={Dahomey} durationInFrames={TL.total_frames} fps={30} width={1920} height={1080} />;
