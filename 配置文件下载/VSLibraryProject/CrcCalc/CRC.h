//extern "C"/*��C�ķ�ʽ������κ���*/ __declspec(dllexport)/*��һ����������Ϊ��������������˵�������Ҫ������������ã�����ΪDLL��һ�����⺯���ӿڡ�*/
//#pragma once

//#define DLL_API extern "C" __declspec(dllexport)
#define DLL_API __declspec(dllexport)


DLL_API unsigned short GetCRC16(char *Buffer, unsigned long Len);
DLL_API unsigned long GetCRC32(unsigned char *Buffer, unsigned long Len);
//DLL_API int add(int a, int b);

