# Mujoco simulation of the hand

Contains the Mujoco model and assets along with a Python node which sets the inverse kinematics problem.

[Mink](https://github.com/kevinzakka/mink) is used to solve the IK as a QP problem.

We can chose to either control the fingertips position (useful for the hand tracking demo) or the distal phalanges orientation.

The AmazingHand model was exported from CAD using [onshape-to-robot](https://github.com/Rhoban/onshape-to-robot)
