# video_generator/advanced_audio_effects.py - Advanced audio effects and processing
import os
import tempfile
import subprocess
import uuid
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

class AudioEffectType(Enum):
    REVERB = "reverb"
    ECHO = "echo"
    CHORUS = "chorus"
    COMPRESSOR = "compressor"
    EQ = "equalizer"
    DISTORTION = "distortion"
    PITCH_SHIFT = "pitch_shift"
    TIME_STRETCH = "time_stretch"
    NOISE_GATE = "noise_gate"
    LIMITER = "limiter"
    STEREO_ENHANCE = "stereo_enhance"
    BASS_BOOST = "bass_boost"
    VOCAL_ENHANCE = "vocal_enhance"
    AMBIENT = "ambient"
    VINTAGE = "vintage"

@dataclass
class AudioEffect:
    type: AudioEffectType
    parameters: Dict[str, Any]
    intensity: float = 1.0  # 0.0 to 1.0
    enabled: bool = True

@dataclass
class AudioEffectPreset:
    name: str
    description: str
    effects: List[AudioEffect]
    category: str
    recommended_for: List[str]

class AdvancedAudioEffects:
    """Advanced audio effects processing system"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.ffmpeg_path = self._find_ffmpeg()
        self.presets = self._initialize_presets()
        
        print("✅ Advanced Audio Effects initialized")
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        possible_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        raise Exception("FFmpeg not found. Please install FFmpeg.")
    
    def _initialize_presets(self) -> Dict[str, AudioEffectPreset]:
        """Initialize audio effect presets"""
        presets = {}
        
        # Thai Voice Enhancement Presets
        presets['thai_voice_powerful'] = AudioEffectPreset(
            name="Thai Voice Powerful",
            description="เสียงพากย์ไทยที่ทรงพลังและกระชับใจ",
            category="voice",
            recommended_for=["motivation", "stoic_content"],
            effects=[
                AudioEffect(
                    type=AudioEffectType.EQ,
                    parameters={
                        'low_freq': 100,
                        'low_gain': -2,
                        'mid_freq': 2000,
                        'mid_gain': 3,
                        'high_freq': 8000,
                        'high_gain': 2
                    },
                    intensity=0.8
                ),
                AudioEffect(
                    type=AudioEffectType.COMPRESSOR,
                    parameters={
                        'threshold': -18,
                        'ratio': 3.5,
                        'attack': 0.003,
                        'release': 0.1
                    },
                    intensity=0.9
                ),
                AudioEffect(
                    type=AudioEffectType.VOCAL_ENHANCE,
                    parameters={
                        'clarity': 0.7,
                        'presence': 0.6
                    },
                    intensity=0.8
                )
            ]
        )
        
        presets['thai_voice_gentle'] = AudioEffectPreset(
            name="Thai Voice Gentle",
            description="เสียงพากย์ไทยที่อ่อนโยนและสงบ",
            category="voice",
            recommended_for=["lofi", "relaxation"],
            effects=[
                AudioEffect(
                    type=AudioEffectType.EQ,
                    parameters={
                        'low_freq': 80,
                        'low_gain': 1,
                        'mid_freq': 1500,
                        'mid_gain': 2,
                        'high_freq': 10000,
                        'high_gain': -1
                    },
                    intensity=0.6
                ),
                AudioEffect(
                    type=AudioEffectType.REVERB,
                    parameters={
                        'room_size': 0.3,
                        'damping': 0.7,
                        'wet_level': 0.2
                    },
                    intensity=0.5
                ),
                AudioEffect(
                    type=AudioEffectType.COMPRESSOR,
                    parameters={
                        'threshold': -20,
                        'ratio': 2.5,
                        'attack': 0.01,
                        'release': 0.3
                    },
                    intensity=0.6
                )
            ]
        )
        
        # Music Enhancement Presets
        presets['lofi_vintage'] = AudioEffectPreset(
            name="Lofi Vintage",
            description="เอฟเฟกต์ Lofi แบบคลาสสิก",
            category="music",
            recommended_for=["lofi", "chill"],
            effects=[
                AudioEffect(
                    type=AudioEffectType.VINTAGE,
                    parameters={
                        'warmth': 0.7,
                        'saturation': 0.5,
                        'vinyl_noise': 0.3
                    },
                    intensity=0.8
                ),
                AudioEffect(
                    type=AudioEffectType.EQ,
                    parameters={
                        'low_freq': 60,
                        'low_gain': 2,
                        'mid_freq': 3000,
                        'mid_gain': -2,
                        'high_freq': 12000,
                        'high_gain': -3
                    },
                    intensity=0.7
                ),
                AudioEffect(
                    type=AudioEffectType.COMPRESSOR,
                    parameters={
                        'threshold': -16,
                        'ratio': 4.0,
                        'attack': 0.02,
                        'release': 0.2
                    },
                    intensity=0.6
                )
            ]
        )
        
        presets['motivation_boost'] = AudioEffectPreset(
            name="Motivation Boost",
            description="เพิ่มพลังและความชัดเจนสำหรับเพลง BGM",
            category="music",
            recommended_for=["motivation", "energy"],
            effects=[
                AudioEffect(
                    type=AudioEffectType.EQ,
                    parameters={
                        'low_freq': 80,
                        'low_gain': 1,
                        'mid_freq': 2500,
                        'mid_gain': 1,
                        'high_freq': 8000,
                        'high_gain': 2
                    },
                    intensity=0.7
                ),
                AudioEffect(
                    type=AudioEffectType.STEREO_ENHANCE,
                    parameters={
                        'width': 1.2,
                        'bass_mono': True
                    },
                    intensity=0.6
                ),
                AudioEffect(
                    type=AudioEffectType.LIMITER,
                    parameters={
                        'threshold': -1,
                        'release': 0.05
                    },
                    intensity=0.8
                )
            ]
        )
        
        # Ambient and Spatial Presets
        presets['ambient_space'] = AudioEffectPreset(
            name="Ambient Space",
            description="สร้างบรรยากาศอันกว้างใหญ่",
            category="ambient",
            recommended_for=["meditation", "ambient"],
            effects=[
                AudioEffect(
                    type=AudioEffectType.REVERB,
                    parameters={
                        'room_size': 0.8,
                        'damping': 0.3,
                        'wet_level': 0.4,
                        'early_reflections': 0.6
                    },
                    intensity=0.9
                ),
                AudioEffect(
                    type=AudioEffectType.CHORUS,
                    parameters={
                        'rate': 0.5,
                        'depth': 0.3,
                        'delay': 0.025
                    },
                    intensity=0.4
                ),
                AudioEffect(
                    type=AudioEffectType.EQ,
                    parameters={
                        'low_freq': 40,
                        'low_gain': -2,
                        'mid_freq': 1000,
                        'mid_gain': -1,
                        'high_freq': 15000,
                        'high_gain': 1
                    },
                    intensity=0.6
                )
            ]
        )
        
        return presets
    
    def apply_preset(self, audio_path: str, preset_name: str, output_path: str = None) -> str:
        """Apply audio effect preset to audio file"""
        if preset_name not in self.presets:
            raise ValueError(f"Preset '{preset_name}' not found")
        
        preset = self.presets[preset_name]
        
        if not output_path:
            output_filename = f"processed_{uuid.uuid4().hex[:8]}.mp3"
            output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Build FFmpeg filter chain
            filter_chain = self._build_filter_chain(preset.effects)
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', audio_path,
                '-filter_complex', filter_chain,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Audio effect processing failed: {result.stderr}")
            
            print(f"✅ Applied preset '{preset_name}' to audio")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Failed to apply preset '{preset_name}': {e}")
    
    def apply_custom_effects(self, audio_path: str, effects: List[AudioEffect], output_path: str = None) -> str:
        """Apply custom list of audio effects"""
        if not output_path:
            output_filename = f"custom_effects_{uuid.uuid4().hex[:8]}.mp3"
            output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Filter enabled effects
            enabled_effects = [effect for effect in effects if effect.enabled]
            
            if not enabled_effects:
                # No effects to apply, just copy file
                import shutil
                shutil.copy2(audio_path, output_path)
                return output_path
            
            # Build filter chain
            filter_chain = self._build_filter_chain(enabled_effects)
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', audio_path,
                '-filter_complex', filter_chain,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Custom effects processing failed: {result.stderr}")
            
            print(f"✅ Applied {len(enabled_effects)} custom effects to audio")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Failed to apply custom effects: {e}")
    
    def _build_filter_chain(self, effects: List[AudioEffect]) -> str:
        """Build FFmpeg filter chain from effects list"""
        filters = []
        current_label = "[0:a]"
        
        for i, effect in enumerate(effects):
            if not effect.enabled:
                continue
            
            next_label = f"[eff{i}]" if i < len(effects) - 1 else ""
            filter_str = self._build_effect_filter(effect, current_label, next_label)
            
            if filter_str:
                filters.append(filter_str)
                current_label = f"[eff{i}]" if next_label else ""
        
        return ";".join(filters) if filters else "[0:a]anull"
    
    def _build_effect_filter(self, effect: AudioEffect, input_label: str, output_label: str) -> str:
        """Build FFmpeg filter string for a single effect"""
        intensity = effect.intensity
        params = effect.parameters
        
        if effect.type == AudioEffectType.EQ:
            # Parametric equalizer
            eq_filters = []
            if 'low_freq' in params and 'low_gain' in params:
                gain = params['low_gain'] * intensity
                eq_filters.append(f"bass=g={gain}:f={params['low_freq']}:w=1")
            if 'mid_freq' in params and 'mid_gain' in params:
                gain = params['mid_gain'] * intensity
                eq_filters.append(f"equalizer=f={params['mid_freq']}:g={gain}:w=1")
            if 'high_freq' in params and 'high_gain' in params:
                gain = params['high_gain'] * intensity
                eq_filters.append(f"treble=g={gain}:f={params['high_freq']}:w=1")
            
            filter_chain = ",".join(eq_filters) if eq_filters else "anull"
            return f"{input_label}{filter_chain}{output_label}"
        
        elif effect.type == AudioEffectType.COMPRESSOR:
            # Dynamic range compression
            threshold = params.get('threshold', -20)
            ratio = params.get('ratio', 3.0) * intensity
            attack = params.get('attack', 0.003)
            release = params.get('release', 0.1)
            
            return f"{input_label}compand=0.3|0.3:1|1:{threshold}/-40|-40/-30|-20/-20:6:0:{threshold}:0.2{output_label}"
        
        elif effect.type == AudioEffectType.REVERB:
            # Reverb effect
            room_size = params.get('room_size', 0.5) * intensity
            damping = params.get('damping', 0.5)
            wet_level = params.get('wet_level', 0.3) * intensity
            
            return f"{input_label}aecho=0.8:0.9:{int(room_size*1000)}:{wet_level}{output_label}"
        
        elif effect.type == AudioEffectType.CHORUS:
            # Chorus effect
            rate = params.get('rate', 1.0)
            depth = params.get('depth', 0.25) * intensity
            delay = params.get('delay', 0.04)
            
            return f"{input_label}chorus=0.5:0.9:{int(delay*1000)}:0.6:0.6:2:2{output_label}"
        
        elif effect.type == AudioEffectType.LIMITER:
            # Limiting
            threshold = params.get('threshold', -1)
            release = params.get('release', 0.05)
            
            return f"{input_label}alimiter=level_in=1:level_out=1:limit={threshold}:attack=5:release={int(release*1000)}{output_label}"
        
        elif effect.type == AudioEffectType.STEREO_ENHANCE:
            # Stereo enhancement
            width = params.get('width', 1.2) * intensity
            
            return f"{input_label}extrastereo=m={width}:c=0{output_label}"
        
        elif effect.type == AudioEffectType.BASS_BOOST:
            # Bass enhancement
            gain = params.get('gain', 3) * intensity
            freq = params.get('frequency', 100)
            
            return f"{input_label}bass=g={gain}:f={freq}:w=1{output_label}"
        
        elif effect.type == AudioEffectType.VOCAL_ENHANCE:
            # Vocal presence enhancement
            clarity = params.get('clarity', 0.5) * intensity
            presence = params.get('presence', 0.5) * intensity
            
            # Combine mid-frequency boost with subtle compression
            filters = [
                f"equalizer=f=3000:g={presence*3}:w=2",
                f"equalizer=f=5000:g={clarity*2}:w=1.5"
            ]
            
            return f"{input_label}{','.join(filters)}{output_label}"
        
        elif effect.type == AudioEffectType.VINTAGE:
            # Vintage/analog warmth
            warmth = params.get('warmth', 0.5) * intensity
            saturation = params.get('saturation', 0.3) * intensity
            vinyl_noise = params.get('vinyl_noise', 0.2) * intensity
            
            # Simulate vintage characteristics
            filters = [
                f"bass=g={warmth*2}:f=100:w=1",
                f"treble=g={-warmth*1.5}:f=8000:w=1",
                f"compand=0.1|0.1:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2"
            ]
            
            return f"{input_label}{','.join(filters)}{output_label}"
        
        elif effect.type == AudioEffectType.NOISE_GATE:
            # Noise gate
            threshold = params.get('threshold', -40)
            ratio = params.get('ratio', 10) * intensity
            
            return f"{input_label}compand=0.02|0.02:0.05|0.05:{threshold}/-90|{threshold}/-30:6:0.25:{threshold}:0.1{output_label}"
        
        elif effect.type == AudioEffectType.PITCH_SHIFT:
            # Pitch shifting
            semitones = params.get('semitones', 0) * intensity
            
            if abs(semitones) > 0.1:
                return f"{input_label}asetrate=44100*2^({semitones}/12),aresample=44100{output_label}"
            else:
                return f"{input_label}anull{output_label}"
        
        else:
            # Unknown effect, pass through
            return f"{input_label}anull{output_label}"
    
    def analyze_audio_spectrum(self, audio_path: str) -> Dict:
        """Analyze audio spectrum and characteristics"""
        try:
            # Use FFmpeg to analyze audio
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-f', 'lavfi',
                '-i', f'amovie={audio_path},astats=metadata=1:reset=1',
                '-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level',
                '-of', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                frames = data.get('frames', [])
                
                if frames:
                    # Extract audio characteristics
                    rms_levels = []
                    peak_levels = []
                    
                    for frame in frames:
                        tags = frame.get('tags', {})
                        if 'lavfi.astats.Overall.RMS_level' in tags:
                            rms_levels.append(float(tags['lavfi.astats.Overall.RMS_level']))
                        if 'lavfi.astats.Overall.Peak_level' in tags:
                            peak_levels.append(float(tags['lavfi.astats.Overall.Peak_level']))
                    
                    return {
                        'average_rms': sum(rms_levels) / len(rms_levels) if rms_levels else 0,
                        'peak_level': max(peak_levels) if peak_levels else 0,
                        'dynamic_range': max(peak_levels) - min(rms_levels) if peak_levels and rms_levels else 0,
                        'suggested_effects': self._suggest_effects_from_analysis(rms_levels, peak_levels)
                    }
            
            return {'error': 'Analysis failed'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _suggest_effects_from_analysis(self, rms_levels: List[float], peak_levels: List[float]) -> List[str]:
        """Suggest effects based on audio analysis"""
        suggestions = []
        
        if not rms_levels or not peak_levels:
            return suggestions
        
        avg_rms = sum(rms_levels) / len(rms_levels)
        max_peak = max(peak_levels)
        dynamic_range = max_peak - min(rms_levels)
        
        # Suggest based on analysis
        if avg_rms < -30:
            suggestions.append("Volume boost recommended")
            suggestions.append("Apply compression to increase loudness")
        
        if dynamic_range > 40:
            suggestions.append("High dynamic range - consider gentle compression")
        elif dynamic_range < 10:
            suggestions.append("Low dynamic range - consider parallel compression")
        
        if max_peak > -3:
            suggestions.append("Limiting recommended to prevent clipping")
        
        return suggestions
    
    def get_available_presets(self, category: str = None) -> List[Dict]:
        """Get list of available effect presets"""
        presets_list = []
        
        for name, preset in self.presets.items():
            if category and preset.category != category:
                continue
            
            preset_info = {
                'name': name,
                'display_name': preset.name,
                'description': preset.description,
                'category': preset.category,
                'recommended_for': preset.recommended_for,
                'effects_count': len(preset.effects)
            }
            presets_list.append(preset_info)
        
        return presets_list
    
    def create_custom_preset(self, name: str, effects: List[AudioEffect], 
                           description: str = "", category: str = "custom") -> bool:
        """Create custom effect preset"""
        try:
            preset = AudioEffectPreset(
                name=name,
                description=description,
                category=category,
                recommended_for=["custom"],
                effects=effects
            )
            
            self.presets[name.lower().replace(' ', '_')] = preset
            print(f"✅ Custom preset '{name}' created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create preset: {e}")
            return False

# Test function
def test_advanced_audio_effects():
    """Test advanced audio effects capabilities"""
    print("🎵 Testing Advanced Audio Effects...")
    
    try:
        effects = AdvancedAudioEffects()
        
        print("✅ Advanced Audio Effects initialized")
        
        # Test preset listing
        presets = effects.get_available_presets()
        print(f"Available presets: {len(presets)}")
        
        for preset in presets[:3]:  # Show first 3
            print(f"  - {preset['display_name']}: {preset['description']}")
        
        print("✅ Advanced Audio Effects tests completed")
        
    except Exception as e:
        print(f"❌ Advanced Audio Effects test failed: {e}")

if __name__ == "__main__":
    test_advanced_audio_effects()