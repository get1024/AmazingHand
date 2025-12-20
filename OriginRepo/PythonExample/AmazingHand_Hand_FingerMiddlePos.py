import time
import numpy as np

from rustypot import Scs0009PyController


ID_1 = 1 #Change to servo ID you want to calibrate 
ID_2 = 2 #Change to servo ID you want to calibrate 
MiddlePos_1 = 0 #Middle position for servo ID_1 
MiddlePos_2 = 0 #Middle position for servo ID_2


c = Scs0009PyController(
        serial_port="COM11",
        baudrate=1000000,
        timeout=0.5,
    )

def main():
    

    c.write_torque_enable(ID_1, 1) 
    c.write_torque_enable(ID_2, 1) 
    #1 = On / 2 = Off / 3 = Free
    
    while True:
    
        ServosInMiddle()
        time.sleep(3)




def ServosInMiddle ():
    
    c.write_goal_speed(ID_1, 6) # Set speed for ID_1 to 6 => Max Speed
    c.write_goal_speed(ID_2, 6) # Set speed for ID_1 to 6 => Max Speed
    Pos_1 = np.deg2rad(MiddlePos_1)
    Pos_2 = np.deg2rad(MiddlePos_2)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    time.sleep(0.01)



if __name__ == '__main__':
    main()


