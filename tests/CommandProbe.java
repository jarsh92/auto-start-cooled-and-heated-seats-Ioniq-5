package com.nemesis.coldstart;
public final class CommandProbe {
    public static void main(String[] a) {
        String command;
        if (a[0].equals("heat")) command = SeatCommands.heating(Boolean.parseBoolean(a[1]), Integer.parseInt(a[2]), Integer.parseInt(a[3]));
        else if (a[0].equals("vent")) command = SeatCommands.ventilation(Integer.parseInt(a[1]), Integer.parseInt(a[2]));
        else if (a[0].equals("driver")) command = SeatCommands.singleVent(true, Integer.parseInt(a[1]));
        else if (a[0].equals("passenger")) command = SeatCommands.singleVent(false, Integer.parseInt(a[1]));
        else if (a[0].equals("driver_heat")) command = SeatCommands.singleHeat(true, Integer.parseInt(a[1]));
        else if (a[0].equals("passenger_heat")) command = SeatCommands.singleHeat(false, Integer.parseInt(a[1]));
        else if (a[0].equals("read")) command = SeatCommands.read();
        else if (a[0].equals("save")) command = SeatCommands.save(true, 62, true, 3, 3, false, true, 67, 3, 0, true);
        else if (a[0].equals("oversize")) command = SeatCommands.shortRequest(new String(new char[768]).replace('\0','x'));
        else command = SeatCommands.off();
        System.out.print(command);
    }
}
