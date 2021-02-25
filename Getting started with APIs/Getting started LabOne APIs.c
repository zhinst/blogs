/*Getting started with APIs – C
 This code reproduces the example shown in Zurich Instruments' video
 introduction to its textual APIs.
 
 The example is simple: it creates a connection to an instrument pre-configured
 through the LabOne graphical user interface, it reads a single sample from
 a demodulator and it closes the connection.

 Please note that no error handling is considered in this simple example;
 for more information on this important topic, please refer to the Zurich
 Instruments Programming Manual.

 Copyright (C) 2021 Zurich Instruments
 This software may be modified and distributed under the terms
 of the MIT license. See the LICENSE file for details.
 */


#include "ziAPI.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
    ZIConnection conn;
    const char server_address[] = "localhost";
    //Initialize the connection
    ziAPIInit(&conn);

    // Connect to the Data Server: use port 8005 for HF2LI and 8004 for the others
    // HF2 only support ZI_API_VERSION_1
    const int port = 8004;
    ziAPIConnectEx(conn, server_address, port, ZI_API_VERSION_6, NULL);

    // Read out a single sample from a demodulator
    // Please change the device ID "/devXXXX/..." matching your instrument's
    ZIDemodSample sample;
    const char demod_path[] = "/devXXXX/demods/0/sample";
    ziAPIGetDemodSample(conn, demod_path, &sample);
    printf("X = %f, Y = %f\n", sample.x, sample.y);

    // Convert X and Y into polar representation
    float r = sqrt(sample.x * sample.x + sample.y * sample.y);
    float theta = atan2(sample.y, sample.x); // Angle in radians

    printf("R = %f V\n", r);
    printf("theta = %f\n", theta);

    //Disconnect from the data server
    ziAPIDisconnect(conn);

    //Destroy the ZIConnection
    ziAPIDestroy(conn);

    return EXIT_SUCCESS;
}
