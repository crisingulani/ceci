from ceci.main import run
from parsl import clear
import tempfile
import os
import pytest
import subprocess

from ceci.pipeline import Pipeline
from ceci_example.example_stages import *
from ceci.config import StageConfig


def test_config():
    config_options = {'chunk_rows': 5000, 'something':float, 'free':None}
    config = StageConfig(**config_options)

    assert config['chunk_rows'] == 5000
    assert config.chunk_rows == 5000
    assert getattr(config, 'chunk_rows') == 5000

    config.chunk_rows = 133
    assert config.chunk_rows == 133

    config.free = 'dog'
    config.free = 42
    
    try:
        config.chunk_rows = 'a'
    except TypeError:
        pass
    else:
        raise RuntimeError("Failed to catch a type error")

    try:
        config['chunk_rows'] = 'a'
    except TypeError:
        pass
    else:
        raise RuntimeError("Failed to catch a type error")
    assert config.chunk_rows == 133

    config['new_par'] = 'abc'
    assert config['new_par'] == 'abc'
    assert config.get_type('new_par') == str
    
    config.reset()
    assert config.chunk_rows == 5000
    
    assert config.get_type('chunk_rows') == int
    

def test_interactive():

    # Load the pipeline interactively, this is just a temp fix to
    # get the run_config and stage_config
    pipeline = Pipeline.read('tests/test.yml')
    # pipeline.run()

    dry_pipe = Pipeline.read('tests/test.yml', dry_run=True)
    dry_pipe.run()
    
    pipe2 = Pipeline.interactive()
    overall_inputs = {'DM':'./tests/inputs/dm.txt',
                      'fiducial_cosmology':'./tests/inputs/fiducial_cosmology.txt'}
    inputs = overall_inputs.copy()
    inputs['metacalibration'] = True
    inputs['config'] = None
    
    pipe2.pipeline_files.update(**inputs)
    pipe2.build_stage(PZEstimationPipe)
    pipe2.build_stage(shearMeasurementPipe, apply_flag=False)
    pipe2.build_stage(WLGCSelector, zbin_edges=[0.2, 0.3, 0.5], ra_range=[-5, 5])
    pipe2.build_stage(SysMapMaker)
    pipe2.build_stage(SourceSummarizer)
    pipe2.build_stage(WLGCCov, aliases= dict(covariance='covariance_copy'))
    pipe2.build_stage(WLGCRandoms)
    pipe2.build_stage(WLGCTwoPoint)
    pipe2.build_stage(WLGCSummaryStatistic, aliases=dict(covariance='covariance_copy'))

    assert len(pipe2.WLGCCov.outputs) == 1

    pipe2.load_configs(overall_inputs, pipeline.run_config, pipeline.stages_config)

    pipe2.print_stages()
    pipe2.WLGCCov.print_io()

    rpr = repr(pipe2.WLGCCov.config)
    
    path = pipe2.pipeline_files.get_path('covariance_copy')
    assert pipe2.pipeline_files.get_tag(path) == 'covariance_copy'
    assert pipe2.pipeline_files.get_type('covariance_copy') == pipe2.WLGCCov.get_output_type('covariance')
    
    pipe2.run()



def test_inter_pipe():

    pipe2 = Pipeline.interactive()
    overall_inputs = {'DM':'./tests/inputs/dm.txt',
                      'fiducial_cosmology':'./tests/inputs/fiducial_cosmology.txt'}
    inputs = overall_inputs.copy()
    inputs['config'] = None

    pipe2.pipeline_files.update(**inputs)
    
    pipe2.build_stage(PZEstimationPipe, name='bob')
    assert isinstance(pipe2.bob, PZEstimationPipe)
    pipe2.remove_stage('bob')

    assert not hasattr(pipe2, 'bob')

    

    
    

    
if __name__ == "__main__":
    test_config()
    test_interactive()
