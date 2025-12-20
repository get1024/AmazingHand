# Motor control node

The motor configuration is set in a TOML file (cf. [r_hand.toml](config/r_hand.toml)).
In this file you can set the motors ID, and angle offsets for each finger.

# Tools
- *change_id*: to help you change the id of a motor. `cargo run --bin=change_id -- -h` for a list of parameters
- *goto*: to move a single motor to a given position. `cargo run --bin=goto -- -h` for a list of parameters
- *get_zeros*: to help you set the motor zeros, it sets the motors in the compliant mode and write the TOML file to the console. `cargo run --bin=get_zeros -- -h` for a list of parameters
- *set_zeros*: to move the hand in the "zero" position according to the config file. `cargo run --bin=set_zeros -- -h` for a list of parameters
