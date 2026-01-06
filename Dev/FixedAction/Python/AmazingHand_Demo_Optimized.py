import time
import numpy as np

from rustypot import Scs0009PyController

class AmazingHand:
    def __init__(self, port="COM3", baudrate=1000000, side=1):
        # Side
        self.Side = side # 1=> Right Hand // 2=> Left Hand

        # Speed
        self.MaxSpeed = 7
        self.CloseSpeed = 3

        # Fingers middle poses
        # replace values by your calibration results
        self.MiddlePos = [3, 0, -5, -8, -2, 5, -12, 0] 

        self.c = Scs0009PyController(
                serial_port=port,
                baudrate=baudrate,
                timeout=0.5,
            )
        
        # Initialize
        # 1 = On / 2 = Off / 3 = Free
        try:
            self.c.write_torque_enable(1, 1)
        except Exception as e:
            print(f"Warning during initialization: {e}")

    def OpenHand(self):
        self.Move_Index (-35,35, self.MaxSpeed)
        self.Move_Middle (-35,35, self.MaxSpeed)
        self.Move_Ring (-35,35, self.MaxSpeed)
        self.Move_Thumb (-35,35, self.MaxSpeed)

    def CloseHand(self):
        self.Move_Index (90,-90, self.CloseSpeed)
        self.Move_Middle (90,-90, self.CloseSpeed)
        self.Move_Ring (90,-90, self.CloseSpeed)
        self.Move_Thumb (90,-90, self.CloseSpeed+1)

    def OpenHand_Progressive(self):
        self.Move_Index (-35,35, self.MaxSpeed-2)
        time.sleep(0.2)
        self.Move_Middle (-35,35, self.MaxSpeed-2)
        time.sleep(0.2)
        self.Move_Ring (-35,35, self.MaxSpeed-2)
        time.sleep(0.2)
        self.Move_Thumb (-35,35, self.MaxSpeed-2)

    def SpreadHand(self):
        if (self.Side==1): # Right Hand
            self.Move_Index (4, 90, self.MaxSpeed)
            self.Move_Middle (-32, 32, self.MaxSpeed)
            self.Move_Ring (-90, -4, self.MaxSpeed)
            self.Move_Thumb (-90, -4, self.MaxSpeed)  
    
        if (self.Side==2): # Left Hand
            self.Move_Index (-60, 0, self.MaxSpeed)
            self.Move_Middle (-35, 35, self.MaxSpeed)
            self.Move_Ring (-4, 90, self.MaxSpeed)
            self.Move_Thumb (-4, 90, self.MaxSpeed)  
    
    def ClenchHand(self):
        if (self.Side==1): # Right Hand
            self.Move_Index (-60, 0, self.MaxSpeed)
            self.Move_Middle (-35, 35, self.MaxSpeed)
            self.Move_Ring (0, 70, self.MaxSpeed)
            self.Move_Thumb (-4, 90, self.MaxSpeed)  
    
        if (self.Side==2): # Left Hand
            self.Move_Index (0, 60, self.MaxSpeed)
            self.Move_Middle (-35, 35, self.MaxSpeed)
            self.Move_Ring (-70, 0, self.MaxSpeed)
            self.Move_Thumb (-90, -4, self.MaxSpeed)
    
    def Index_Pointing(self):
        self.Move_Index (-40, 40, self.MaxSpeed)
        self.Move_Middle (90, -90, self.MaxSpeed)
        self.Move_Ring (90, -90, self.MaxSpeed)
        self.Move_Thumb (90, -90, self.MaxSpeed)
    
    def Nonono(self):
        self.Index_Pointing()
        for i in range(3) :
            time.sleep(0.2)
            self.Move_Index (-10, 80, self.MaxSpeed)
            time.sleep(0.2)
            self.Move_Index (-80, 10, self.MaxSpeed)
    
        self.Move_Index (-35, 35, self.MaxSpeed)
        time.sleep(0.4)
    
    def Perfect(self):
        if (self.Side==1): #Right Hand
            self.Move_Index (50, -50, self.MaxSpeed)
            self.Move_Middle (0, -0, self.MaxSpeed)
            self.Move_Ring (-20, 20, self.MaxSpeed)
            self.Move_Thumb (65, 12, self.MaxSpeed)

        if (self.Side==2): #Left Hand
            self.Move_Index (50, -50, self.MaxSpeed)
            self.Move_Middle (0, -0, self.MaxSpeed)
            self.Move_Ring (-20, 20, self.MaxSpeed)
            self.Move_Thumb (-12, -65, self.MaxSpeed)
    
    def Victory(self):
        if (self.Side==1): #Right Hand 
            self.Move_Index (-15, 65, self.MaxSpeed)
            self.Move_Middle (-65, 15, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (90, -90, self.MaxSpeed)

        if (self.Side==2): #Left Hand
            self.Move_Index (-65, 15, self.MaxSpeed)
            self.Move_Middle (-15, 65, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (90, -90, self.MaxSpeed)
    
    def Pinched(self):
        if (self.Side==1): #Right Hand
            self.Move_Index (90, -90, self.MaxSpeed)
            self.Move_Middle (90, -90, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (0, -75, self.MaxSpeed)

        if (self.Side==2): #Left Hand
            self.Move_Index (90, -90, self.MaxSpeed)
            self.Move_Middle (90, -90, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (75, 5, self.MaxSpeed)

    def Scissors(self):
        self.Victory();
        if (self.Side==1): #Right Hand
            for i in range(3):  
                time.sleep(0.2)
                self.Move_Index (-50, 20, self.MaxSpeed)
                self.Move_Middle (-20, 50, self.MaxSpeed)
                
                time.sleep(0.2)
                self.Move_Index (-15, 65, self.MaxSpeed)
                self.Move_Middle (-65, 15, self.MaxSpeed)

        if (self.Side==2): #Left Hand
            for i in range(3):
                time.sleep(0.2)
                self.Move_Index (-20, 50, self.MaxSpeed)
                self.Move_Middle (-50, 20, self.MaxSpeed)
                
                time.sleep(0.2)
                self.Move_Index (-65, 15, self.MaxSpeed)
                self.Move_Middle (-15, 65, self.MaxSpeed)

    def Fuck(self):

        if (self.Side==1): #Right Hand
            self.Move_Index (90, -90, self.MaxSpeed)
            self.Move_Middle (-35, 35, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (0, -75, self.MaxSpeed)

        if (self.Side==2): #Left Hand
            self.Move_Index (90, -90, self.MaxSpeed)
            self.Move_Middle (-35, 35, self.MaxSpeed)
            self.Move_Ring (90, -90, self.MaxSpeed)
            self.Move_Thumb (75, 0, self.MaxSpeed)
    
    def Move_Index (self, Angle_1,Angle_2,Speed):
        
        self.c.write_goal_speed(1, Speed)
        time.sleep(0.0002)
        self.c.write_goal_speed(2, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(self.MiddlePos[0]+Angle_1)
        Pos_2 = np.deg2rad(self.MiddlePos[1]+Angle_2)
        self.c.write_goal_position(1, Pos_1)
        self.c.write_goal_position(2, Pos_2)
        time.sleep(0.005)

    def Move_Middle(self, Angle_1,Angle_2,Speed):    
        self.c.write_goal_speed(3, Speed)
        time.sleep(0.0002)
        self.c.write_goal_speed(4, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(self.MiddlePos[2]+Angle_1)
        Pos_2 = np.deg2rad(self.MiddlePos[3]+Angle_2)
        self.c.write_goal_position(3, Pos_1)
        self.c.write_goal_position(4, Pos_2)
        time.sleep(0.005)

    def Move_Ring(self, Angle_1,Angle_2,Speed):    
        self.c.write_goal_speed(5, Speed)
        time.sleep(0.0002)
        self.c.write_goal_speed(6, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(self.MiddlePos[4]+Angle_1)
        Pos_2 = np.deg2rad(self.MiddlePos[5]+Angle_2)
        self.c.write_goal_position(5, Pos_1)
        self.c.write_goal_position(6, Pos_2)
        time.sleep(0.005)

    def Move_Thumb(self, Angle_1,Angle_2,Speed):    
        self.c.write_goal_speed(7, Speed)
        time.sleep(0.0002)
        self.c.write_goal_speed(8, Speed)
        time.sleep(0.0002)
        Pos_1 = np.deg2rad(self.MiddlePos[6]+Angle_1)
        Pos_2 = np.deg2rad(self.MiddlePos[7]+Angle_2)
        self.c.write_goal_position(7, Pos_1)
        self.c.write_goal_position(8, Pos_2)
        time.sleep(0.005)

def main():
    # Example usage
    hand = AmazingHand(side=1)

    # Original loop logic could go here, or just simple demo
    while True:
        hand.OpenHand()

        time.sleep(0.5)

        hand.CloseHand()
        time.sleep(3)

        hand.OpenHand_Progressive()
        time.sleep(0.5)

        hand.SpreadHand()
        time.sleep(0.6)
        hand.ClenchHand()
        time.sleep(0.6)

        hand.OpenHand()
        time.sleep(0.2)

        hand.Index_Pointing()
        time.sleep(0.4)
        hand.Nonono()
        time.sleep(0.5)
        
        hand.OpenHand()
        time.sleep(0.3)

        hand.Perfect()
        time.sleep(0.8)

        hand.OpenHand()
        time.sleep(0.4)

        hand.Victory()
        time.sleep(1)
        hand.Scissors()
        time.sleep(0.5)

        hand.OpenHand()
        time.sleep(0.4)

        hand.Pinched()
        time.sleep(1)

        hand.Fuck()
        time.sleep(0.8)


        #trials

        #c.sync_write_raw_goal_position([1,2], [50,50])
        #time.sleep(1)

        #a=c.read_present_position(1)
        #b=c.read_present_position(2)
        #a=np.rad2deg(a)
        #b=np.rad2deg(b)
        #print(f'{a} {b}')
        #time.sleep(0.001)
        
        time.sleep(1)
        # Add other calls as needed or uncomment below
        # hand.CloseHand()
        # time.sleep(1)

if __name__ == '__main__':
    main()