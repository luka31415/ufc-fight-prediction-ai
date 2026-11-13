import pandas as pd
import pytest
from ufc_ai.regional import calculate_uae_russia_feature as feature, add_feature, is_uae_location

@pytest.mark.parametrize('a,b,expected', [('Russia','Brazil',1),('Brazil','Russian Federation',-1),('Russia','Russia',0),('Brazil','USA',0)])
def test_direction_and_symmetry(a,b,expected):
    assert feature(a,b,event_location='Abu Dhabi, UAE') == expected
    assert feature(b,a,event_location='Abu Dhabi, UAE') == -expected

@pytest.mark.parametrize('flag',[False,0,'False','0'])
def test_false_flags(flag):
    assert feature('Russia','Brazil',is_uae_event=flag) == 0

@pytest.mark.parametrize('flag',[float('nan'),'unknown',2,pd.NA])
def test_bad_flags(flag):
    with pytest.raises(ValueError): feature('Russia','Brazil',is_uae_event=flag)

def test_missing_location_and_country():
    with pytest.raises(ValueError): feature('Russia','Brazil')
    with pytest.raises(ValueError): feature('Russia',None,is_uae_event=True)
    assert not is_uae_location('Xuae City')
    assert is_uae_location('Dubai, U.A.E.')

def test_frame_copy_and_index():
    frame=pd.DataFrame({'A_COUNTRY':['Russia','Russia'],'B_COUNTRY':['Brazil','Brazil'],'flag':['False','True']},index=[8,3])
    out=add_feature(frame,is_uae_col='flag')
    assert out.DIFF_UAE_RUSSIA_HOME.tolist() == [0,1]
    assert out.index.tolist() == [8,3]
    assert 'DIFF_UAE_RUSSIA_HOME' not in frame
