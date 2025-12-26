"""Mujoco Client: This node is used to represent simulated robot, it can be used to read virtual positions, or can be controlled."""

import argparse

import os
import time

import mujoco
import mujoco.viewer
import pyarrow as pa
from dora import Node

import mink
from loop_rate_limiters import RateLimiter
from mink.contrib import TeleopMocap
from pathlib import Path
import numpy as np

ROOT_PATH = Path(os.path.dirname(os.path.abspath(__file__)))


class Client:
    """TODO: Add docstring."""

    def __init__(self, mode='pos'):
        """TODO: Add docstring."""


        self.model = mujoco.MjModel.from_xml_path(
            (ROOT_PATH / "AH_Right/mjcf/scene.xml").as_posix()
        )
        # self.data=mujoco.MjData(self.model)


        self.configuration = mink.Configuration(self.model)

        self.posture_task = mink.PostureTask(self.model, cost=1e-2)

        # lm_damping 是Mujoco Mink 逆运动学（IK）求解器的阻尼参数，
        # 阻尼过高会使求解器为了保持稳定性而限制关节速度，导致仿真
        # 手在尝试“追赶”手部动作时显得非常迟缓和滞后。
        if mode=='pos':
            # pos 是位置控制模式，lm_damping 设为 0.05 是为了在保持稳定性的同时
            # 允许仿真手“追赶”手部动作，而不是立即响应。
            self.task1 = mink.FrameTask(
                frame_name='tip1',
                frame_type="site",
                position_cost=1.0,
                orientation_cost=0.0,
                lm_damping=0.05,
            )

            self.task2 = mink.FrameTask(
                frame_name='tip2',
                frame_type="site",
                position_cost=1.0,
                orientation_cost=0.0,
                lm_damping=0.05,
            )

            self.task3 = mink.FrameTask(
                frame_name='tip3',
                frame_type="site",
                position_cost=1.0,
                orientation_cost=0.0,
                lm_damping=0.05,
            )

            self.task4 = mink.FrameTask(
                frame_name='tip4',
                frame_type="site",
                position_cost=1.0,
                orientation_cost=0.0,
                lm_damping=0.05,
            )
        elif mode=='quat': 
            # quat 是姿态/朝向控制 。IK 求解器只关心指尖的 朝向 (旋转角度) 是否与目标一致，不关心指尖具体在空间中的哪个点
            self.task1 = mink.FrameTask(
                frame_name='tip1',
                frame_type="site",
                position_cost=0.0,
                orientation_cost=1.0,
                lm_damping=1.0,
            )

            self.task2 = mink.FrameTask(
                frame_name='tip2',
                frame_type="site",
                position_cost=0.0,
                orientation_cost=1.0,
                lm_damping=1.0,
            )

            self.task3 = mink.FrameTask(
                frame_name='tip3',
                frame_type="site",
                position_cost=0.0,
                orientation_cost=1.0,
                lm_damping=1.0,
            )

            self.task4 = mink.FrameTask(
                frame_name='tip4',
                frame_type="site",
                position_cost=0.0,
                orientation_cost=1.0,
                lm_damping=1.0,
            )
        else:
            print(f"Error, unknown mode: {mode}")
            return -1
        # Regulate all equality constraints with the same cost.
        eq_task = mink.EqualityConstraintTask(self.model, cost=1000.0)

        self.tasks = [
            eq_task,
            self.posture_task,
            self.task1,
            self.task2,
            self.task3,
            self.task4,
        ]



        self.model = self.configuration.model
        self.data = self.configuration.data
        self.solver = "quadprog"

        self.motor_pos=[]
        self.metadata=[]
        self.node = Node()

    def run(self):
        """TODO: Add docstring."""
        with mujoco.viewer.launch_passive(self.model, self.data) as viewer:

            rate = RateLimiter(frequency=500.0)
            # dt = rate.dt
            # t = 0
            self.configuration.update_from_keyframe("zero")

            # Initialize mocap bodies at their respective sites.
            self.posture_task.set_target_from_configuration(self.configuration)

            mink.move_mocap_to_frame(self.model, self.data, "finger1_target", "tip1", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger2_target", "tip2", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger3_target", "tip3", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger4_target", "tip4", "site")


            for event in self.node:
                event_type = event["type"]

                if event_type == "INPUT":
                    event_id = event["id"]

                    if event_id == "tick":
                        # self.node.send_output("tick", pa.array([]), event["metadata"])

                        if not viewer.is_running():
                            break

                        step_start = time.time()



                        self.task1.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger1_target")
                        )
                        self.task2.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger2_target")
                        )
                        self.task3.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger3_target")
                        )
                        self.task4.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger4_target")
                        )





                        # vel = mink.solve_ik(self.configuration, self.tasks, self.model.opt.timestep, self.solver, 1e-5)
                        # self.configuration.integrate_inplace(vel, self.model.opt.timestep)
                        vel = mink.solve_ik(self.configuration, self.tasks, rate.dt, self.solver, 1e-5)
                        self.configuration.integrate_inplace(vel, rate.dt)



                        # Step the simulation forward
                        # mujoco.mj_step(self.m, self.data)

                        # mujoco.mj_step(self.model, self.data)


                        #get the motors position and send for real motor control

                        f1_motor1=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger1_motor1")
                        f1_motor2=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger1_motor2")
                        f2_motor1=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger2_motor1")
                        f2_motor2=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger2_motor2")
                        f3_motor1=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger3_motor1")
                        f3_motor2=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger3_motor2")
                        f4_motor1=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger4_motor1")
                        f4_motor2=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,"finger4_motor2")
                        # print(f"motor1: {self.data.joint(f1_motor1).qpos} motor2: {self.data.joint(f1_motor2).qpos}")
                        self.metadata=event["metadata"]
                        self.metadata["r_finger1"]=[0,1]
                        self.metadata["r_finger2"]=[2,3]
                        self.metadata["r_finger3"]=[4,5]
                        self.metadata["r_finger4"]=[6,7]

                        self.motor_pos=np.zeros(8);
                        self.motor_pos[self.metadata["r_finger1"]]=np.array([self.data.joint(f1_motor1).qpos[0],self.data.joint(f1_motor2).qpos[0]])
                        self.motor_pos[self.metadata["r_finger2"]]=np.array([self.data.joint(f2_motor1).qpos[0],self.data.joint(f2_motor2).qpos[0]])
                        self.motor_pos[self.metadata["r_finger3"]]=np.array([self.data.joint(f3_motor1).qpos[0],self.data.joint(f3_motor2).qpos[0]])
                        self.motor_pos[self.metadata["r_finger4"]]=np.array([self.data.joint(f4_motor1).qpos[0],self.data.joint(f4_motor2).qpos[0]])



                        viewer.sync()

                        # Rudimentary time keeping, will drift relative to wall clock.
                        # time_until_next_step = self.model.opt.timestep - (
                        #     time.time() - step_start
                        # )
                        # if time_until_next_step > 0:
                        #     time.sleep(time_until_next_step)

                    elif event_id == "pull_position":
                        self.pull_position(self.node, event["metadata"])


                    elif event_id == "tick_ctrl":
                        if len(self.metadata)>0:
                            # print(f"Sending joints pos: {self.motor_pos[:3]}...")
                            self.node.send_output("mj_r_joints_pos", pa.array(self.motor_pos), self.metadata)
                        # self.pull_position(self.node, event["metadata"])

                    elif event_id == "pull_velocity":
                        self.pull_velocity(self.node, event["metadata"])
                    elif event_id == "pull_current":
                        self.pull_current(self.node, event["metadata"])
                    elif event_id == "write_goal_position":
                        self.write_goal_position(event["value"])
                    elif event_id == "hand_pos" or event_id == "r_hand_pos":
                        # print(f"Received hand pos: {event['value']}")
                        try:
                            self.write_mocap_pos(event["value"])
                            # print(f"Updated mocap: {self.data.mocap_pos[0]}")
                        except Exception as e:
                            print(f"Error updating mocap: {e}")
                    elif event_id == "r_hand_quat":
                        self.write_mocap_quat(event["value"])

                    elif event_id == "end":
                        break

                elif event_type == "ERROR":
                    raise ValueError(
                        "An error occurred in the dataflow: " + event["error"],
                    )

            self.node.send_output("end", pa.array([]))

    def pull_position(self, node, metadata):
        """TODO: Add docstring."""

    def pull_velocity(self, node, metadata):
        """TODO: Add docstring."""

    def pull_current(self, node, metadata):
        """TODO: Add docstring."""

    def write_goal_position(self, goal_position_with_joints):
        """TODO: Add docstring."""
        joints = goal_position_with_joints.field("joints")
        goal_position = goal_position_with_joints.field("values")

        for i, joint in enumerate(joints):
            self.data.joint(joint.as_py()).qpos[0] = goal_position[i].as_py()

    def write_mocap_pos(self, hand):

        #please, a method to access the mocap objects by name...

        if "r_tip1" in hand[0]:
            [x,y,z]=hand[0]['r_tip1'].values
            self.data.mocap_pos[0]=[x.as_py()*1.5-0.025,y.as_py()*1.5+0.022,z.as_py()*1.5+0.098]
        if "r_tip2" in hand[0]:
            [x,y,z]=hand[0]['r_tip2'].values
            self.data.mocap_pos[1]=[x.as_py()*1.5-0.025,y.as_py()*1.5-0.009,z.as_py()*1.5+0.092]
        if "r_tip3" in hand[0]:
            [x,y,z]=hand[0]['r_tip3'].values
            self.data.mocap_pos[2]=[x.as_py()*1.5-0.025,y.as_py()*1.5-0.040,z.as_py()*1.5+0.082]
        if "r_tip4" in hand[0]:
            [x,y,z]=hand[0]['r_tip4'].values
            self.data.mocap_pos[3]=[x.as_py()*1.5+0.024,y.as_py()*1.5+0.019,z.as_py()*1.5+0.017]


    def write_mocap_quat(self, hand):
        #please, a method to access the mocap objects by name...

        if "r_tip1" in hand[0]:
            [w,x,y,z]=hand[0]['r_tip1'].values
            self.data.mocap_quat[0]=[w.as_py(),x.as_py(),y.as_py(),z.as_py()]
        if "r_tip2" in hand[0]:
            [w,x,y,z]=hand[0]['r_tip2'].values
            self.data.mocap_quat[1]=[w.as_py(),x.as_py(),y.as_py(),z.as_py()]
        if "r_tip3" in hand[0]:
            [w,x,y,z]=hand[0]['r_tip3'].values
            self.data.mocap_quat[2]=[w.as_py(),x.as_py(),y.as_py(),z.as_py()]
        if "r_tip4" in hand[0]:
            [w,x,y,z]=hand[0]['r_tip4'].values
            self.data.mocap_quat[3]=[w.as_py(),x.as_py(),y.as_py(),z.as_py()]




def main():
    """Handle dynamic nodes, ask for the name of the node in the dataflow."""

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", type=str, choices=['pos','quat'], default='pos',
                    help="control mode: pos=position (we control the position of the tip) quat=quaternion (we control the orientation of the tip)")
    args = parser.parse_args()
    client = Client(args.mode)
    client.run()


if __name__ == "__main__":
    main()
