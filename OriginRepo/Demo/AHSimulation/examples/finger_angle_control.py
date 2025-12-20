import numpy as np
import pyarrow as pa
from dora import Node

from scipy.spatial.transform import Rotation
import time

def main():

    node = Node()


    pa.array([])  # initialize pyarrow array


    t0=time.time()
    for event in node:

        event_type = event["type"]

        if event_type == "INPUT":
            event_id = event["id"]

            if event_id == "tick":
                elapsed=time.time()-t0
                s1_pitch=np.sin(2.0*np.pi*1.0*elapsed)*np.radians(10.0)+np.radians(10.0)
                rs1_roll=np.cos(2.0*np.pi*1.0*elapsed)*np.radians(10.0)
                ls1_roll=np.cos(2.0*np.pi*1.0*elapsed)*np.radians(-10.0)

                s2_pitch=np.sin(2.0*np.pi*1.0*elapsed)*np.radians(140.0/2.0)+np.radians(140.0/2.0)
                s4_pitch=np.sin(2.0*np.pi*1.0*elapsed)*np.radians((90.0+53.0)/2.0)+np.radians((90.0-53.0)/2.0)


                #motors 0° => ~121.9° pitch of the distal phalange in the finger base referential
                #flexion range (distal phalange) [0°, 140°]
                #abduction range [-20°, 20°]

                rtip1=Rotation.from_euler('XYZ',[rs1_roll,s1_pitch,0.0])
                rtip1=rtip1.as_quat(scalar_first=True)

                ltip1=Rotation.from_euler('XYZ',[ls1_roll,s1_pitch,0.0])
                ltip1=ltip1.as_quat(scalar_first=True)


                # tip2=Rotation.from_euler('XYZ',[np.radians(10.0),np.radians(140.0),0.0]) #finger2 has a 10° roll offset
                rtip2=Rotation.from_euler('XYZ',[np.radians(10.0),s2_pitch,0.0]) #finger2 has a 10° roll offset
                rtip2=rtip2.as_quat(scalar_first=True)

                ltip2=Rotation.from_euler('XYZ',[np.radians(-10.0),s2_pitch,0.0]) #finger2 has a 10° roll offset
                ltip2=ltip2.as_quat(scalar_first=True)



                # tip3=Rotation.from_euler('XYZ',[np.radians(20.0),np.radians(140.0),0.0]) #finger3 has a 20° roll offset
                rtip3=Rotation.from_euler('XYZ',[np.radians(20.0),s2_pitch,0.0]) #finger3 has a 20° roll offset
                rtip3=rtip3.as_quat(scalar_first=True)

                ltip3=Rotation.from_euler('XYZ',[np.radians(-20.0),s2_pitch,0.0]) #finger3 has a 20° roll offset
                ltip3=ltip3.as_quat(scalar_first=True)


                # tip4=Rotation.from_euler('XYZ',[0.0,-np.pi/2.0,np.radians(20.0)]) #finger4 has a 20° yaw offset
                rtip4=Rotation.from_euler('xyz',[0.0,-s4_pitch,np.radians(20.0)]) #finger4 has a 20° yaw offset
                rtip4=rtip4.as_quat(scalar_first=True)

                ltip4=Rotation.from_euler('xyz',[0.0,-s4_pitch,np.radians(-20.0)]) #finger4 has a 20° yaw offset
                ltip4=ltip4.as_quat(scalar_first=True)


                # tip2=[1,0,0,0]
                # tip3=[1,0,0,0]
                # tip4=[1,0,0,0]
                angles=[{'r_tip1': rtip1,'r_tip2': rtip2,'r_tip3': rtip3,'r_tip4': rtip4, 'l_tip1': ltip1,'l_tip2': ltip2,'l_tip3': ltip3,'l_tip4': ltip4}]
                # angles=[{'r_tip1': rtip1,'r_tip2': rtip2,'r_tip3': rtip3,'r_tip4': rtip4}]

                node.send_output('hand_quat',pa.array(angles))



        elif event_type == "ERROR":
            raise RuntimeError(event["error"])


if __name__ == "__main__":
    main()
