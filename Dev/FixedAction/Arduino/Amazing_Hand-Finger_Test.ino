#include <SCServo.h>

SCSCL sc;


// Finger parameters
int ID_1 = 1; //Change to servo ID you want to calibrate 
int ID_2 = 2; //Change to servo ID you want to calibrate
int MiddlePos_1 = 511;  // Middle position for servo ID_1
int MiddlePos_2 = 511;  // Middle position for servo ID_2


void setup()
{
  Serial1.begin(1000000);
  //Serial.begin(115200);
  sc.pSerial = &Serial1;
  delay(1000);
}

void loop()
{
  
  CloseFinger();delay(3000);
  OpenFinger();delay(500);
  Nonono();delay(500);

  
  
}

void CloseFinger()
{
  sc.RegWritePos(ID_1, MiddlePos_1+300, 0, 1500); //Servo 1
  sc.RegWritePos(ID_2, MiddlePos_2-300, 0, 1500); //Servo 2
  sc.RegWriteAction(); 
}

void OpenFinger()
{
  sc.RegWritePos(ID_1, MiddlePos_1-100, 0, 1500); //Servo 1
  sc.RegWritePos(ID_2, MiddlePos_2+100, 0, 1500); //Servo 2
  sc.RegWriteAction();  
}

void Nonono()
{
  sc.RegWritePos(ID_1, MiddlePos_1-100, 0, 1500);sc.RegWritePos(ID_2, MiddlePos_2+100, 0, 1500);sc.RegWriteAction(); // Straight right 
  for (int i=0;i<3;i++)
  {
    delay(300);
    sc.RegWritePos(ID_1, MiddlePos_1, 0, 1200);sc.RegWritePos(ID_2, MiddlePos_2+200, 0, 1200);sc.RegWriteAction(); // Straight right
    delay(300);
    sc.RegWritePos(ID_1, MiddlePos_1-200, 0, 1200);sc.RegWritePos(ID_2, MiddlePos_1, 0, 1200);sc.RegWriteAction(); // Straight left
    
  }
  sc.RegWritePos(ID_1, MiddlePos_1-100, 0, 1500);sc.RegWritePos(ID_2, MiddlePos_1+100, 0, 1500);sc.RegWriteAction(); // Straight middle
  delay(400);
}