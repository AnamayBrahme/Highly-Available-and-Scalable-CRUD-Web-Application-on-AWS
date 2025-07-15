#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import App, Environment

from iactemp2.iactemp2_stack import Iactemp2Stack
from iactemp2.phase2 import Phase2SingleVMStack
from iactemp2.ph3_1 import Phase3CombinedStack
from iactemp2.ph3_2 import Phase3RdsStack
from iactemp2.ph3_3 import Phase3Step3
from iactemp2.ph4_1 import Phase4Step1

env = Environment(account="528316341503", region="us-east-1")
app = cdk.App()
Phase2SingleVMStack(app,"Phase2SingleVMStack")
Phase3CombinedStack(app,"Phase3CombinedStack")
Phase3RdsStack(app,"Phase3RdsStack",env=env)
Phase3Step3(app,"Phase3Step3",env=env)
Phase4Step1(app,"Phase4Step1",env=env)

Iactemp2Stack(app, "Iactemp2Stack")

app.synth()
