//extern "C"/*以C的方式编译这段函数*/ __declspec(dllexport)/*将一个函数声名为导出函数，就是说这个函数要被其他程序调用，即作为DLL的一个对外函数接口。*/
//#pragma once

//#define DLL_API extern "C" __declspec(dllexport)
#define DLL_API __declspec(dllexport)


DLL_API unsigned short GetCRC16(char *Buffer, unsigned long Len);
DLL_API unsigned long GetCRC32(unsigned char *Buffer, unsigned long Len);
//DLL_API int add(int a, int b);

