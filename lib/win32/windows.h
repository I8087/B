stdcall ExitProcess(errn);
stdcall GetStdHandle(nStdHandle);
stdcall WriteFile(hFile, lpBuffer, nNumberOfBytesToWrite, lpNumberOfBytesWritten, lpOverlapped);
