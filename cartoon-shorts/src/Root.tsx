import {Composition} from 'remotion';
import {SunShort} from './sun/SunShort';
import {FPS, NF} from './sun/timeline';

export const RemotionRoot: React.FC = () => {
	return (
		<Composition id="SunShort" component={SunShort} durationInFrames={NF} fps={FPS} width={1080} height={1920} />
	);
};
