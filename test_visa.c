/////////////////////////////////////////////////////////////////////////////
// Author: Rawat S.
// Date: 2017-12-25
// Description:
//   Demo C code that uses the VISA library to communicat withe
//   Rigol instruments (digital oscilloscope and function generator).
//
/////////////////////////////////////////////////////////////////////////////
// Install the VISA library for Linux / Ubuntu:
//   sudo apt-get install libvisa-dev
//
// Compile:
//   gcc -Wall -std=gnu99 ./test_visa.c -o ./test_visa -lvisa
//
// Run:
//   sudo ./test_visa
/////////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <visa.h>

// specify the Vendor ID and Device ID (hex. string) of the target device
const char VENDOR_ID_STR[] = "0x1ab1";
const char DEVICE_ID_STR[] = "0x04b0";

#define MAX_CNT 1024

// global variables

ViStatus    status;
ViSession   defaultRM, instr;
ViUInt32    retCount;
ViChar      buffer[ MAX_CNT ];
ViFindList  findList;

int writeOnlyInstr( const char *cmd_str ) {
   strcpy( buffer, cmd_str );
   status = viWrite(instr, (ViBuf)buffer, strlen(cmd_str), &retCount );
   if ( status != VI_SUCCESS ) {
     //viStatusDesc( defaultRM, status, buffer );
     fprintf( stderr, "Error: %s\n", buffer );
     return -1;
   }
   return 0;
}

int readOnlyInstr( char *data_buf, int max_len ) {
   status = viRead (instr, (unsigned char *)data_buf, max_len, &retCount);
   if (status != VI_SUCCESS) {
     return -1;
   }
   int len = strlen(data_buf);
   if ( len > 1 ) {
     char last_char = data_buf[len-1];
     if ( last_char == '\n' || last_char == '\r' ) {
       data_buf[len-1] = '\0';  // remove the newline char
     }
   }
   return 0;
}

int writeReadInstr( const char *cmd_str, char *data_buf, int max_len ) {
   int ret_val = writeOnlyInstr( cmd_str );
   if ( !ret_val ) {
      usleep( 100000 ); // sleep for 100 msec
      return readOnlyInstr( data_buf, max_len );
   }
   return ret_val;
}

int check_device( const char *buf, const char *vendor_id, const char *dev_id ) {
   if ( strstr(buf, vendor_id) != NULL && strstr(buf, dev_id) != NULL )
     return 0;
   else
     return -1;
}

int main(void) {
    char selected_device[64];

    // initializing the system
    status = viOpenDefaultRM( &defaultRM );
    if ( status != VI_SUCCESS ) {
       fprintf( stderr, "VISA Initialization FAILED !!!\n" );
       return -1;
    } else {
       fprintf( stdout, "VISA Initialization OK \n" );
    }

    strcpy( buffer, "USB?*::INSTR" );
    viFindRsrc( defaultRM, buffer, &findList, &retCount, buffer );


    if ( retCount > 0 ) {
       int count = 1;
       fprintf( stdout, "Number of device(s) found: %lu\n", retCount );
       while (1) {
          fprintf( stdout, "%d) %s\n", count++, buffer );
          if ( !check_device( buffer, VENDOR_ID_STR, DEVICE_ID_STR ) ) {
             fprintf( stdout, "Found: %s, %s\n", VENDOR_ID_STR, DEVICE_ID_STR );
             strcpy( selected_device, buffer );
          }
          status = viFindNext( findList, buffer );
          if ( status != VI_SUCCESS ) {
             break;
          }
       } // end-of-while

       // Open communication with the target device
       status = viOpen( defaultRM, selected_device, VI_NULL, VI_NULL, &instr );
       if ( status != VI_SUCCESS ) {
         fprintf( stderr, "Open device FAILED !!!\n" );
         return -1;
       }
       else {
         fprintf( stdout, "Open device OK \n" );
       }
    }
    else {
      fprintf( stderr, "No device found \n" );
      return -1;
    }

   // Set the timeout for message-based communication
   status = viSetAttribute( instr, VI_ATTR_TMO_VALUE, 5000 );

   writeOnlyInstr( "*RST\n" ); // send a command to reset the device
   usleep( 1000000 );

   if ( !writeOnlyInstr( "*IDN?\n" ) ) { // get ID string from the device
     usleep( 100000 );
     if ( !readOnlyInstr(buffer, 200) ) {
       fprintf( stdout, "> '%s'\n", buffer );
     }
   }

   if ( !writeReadInstr( "*IDN?\n", buffer, 200 ) ) {
     fprintf( stdout, "> '%s'\n", buffer );
   }

   status = viClose(instr);
   status = viClose(defaultRM);
   usleep( 10000 );

   return 0;
}

/////////////////////////////////////////////////////////////////////////////
