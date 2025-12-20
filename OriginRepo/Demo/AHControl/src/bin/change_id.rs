use clap::Parser;

use rustypot::servo;
// use rustypot::DynamixelProtocolHandler;
use std::{error::Error, thread, time::Duration};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Serialport
    #[arg(short, long, default_value = "/dev/ttyACM0")]
    serialport: String,
    /// baudrate
    #[arg(short, long, default_value_t = 1_000_000)]
    baudrate: u32,
    /// old id
    #[arg(short, long, default_value_t = 1)]
    old_id: u8,
    /// new id
    #[arg(short, long)]
    new_id: u8,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse();
    let serialport: String = args.serialport;
    let baudrate: u32 = args.baudrate;
    let old_id: u8 = args.old_id;
    let new_id: u8 = args.new_id;

    println!("Opening port {serialport} at baudrate {baudrate}");
    println!("Changing id: {old_id} into {new_id}");

    let serial_port = serialport::new(serialport, baudrate)
        .timeout(Duration::from_millis(10))
        .open()?;

    // let dph=DynamixelProtocolHandler::v1();
    let mut controller = servo::feetech::scs0009::Scs0009Controller::new()
        .with_protocol_v1()
        .with_serial_port(serial_port);

    controller.write_id(old_id, new_id)?;
    thread::sleep(Duration::from_millis(1000));
    controller.read_id(new_id)?;
    println!("Quitting");
    Ok(())
}
