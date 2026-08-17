from harness_demo.domain import Lane
from harness_demo.runners.deepseek_provider import run_deepseek_provider_lane
from harness_demo.runners.hand_built import run_hand_built_lane
from harness_demo.runners.raw import run_raw_strong_lane
from harness_demo.runners.strands_sdk import run_strands_sdk_lane

RUNNERS = {
    Lane.RAW_STRONG: run_raw_strong_lane,
    Lane.HAND_BUILT: run_hand_built_lane,
    Lane.STRANDS_SDK: run_strands_sdk_lane,
    Lane.DEEPSEEK_PROVIDER: run_deepseek_provider_lane,
}
