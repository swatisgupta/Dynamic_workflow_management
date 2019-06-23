#ifndef __TAU_GPU_ADAPTER_OPENCL_H__
#define __TAU_GPU_ADAPTER_OPENCL_H__

#include "TauGpu.h"
#include <stdio.h>
#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif
#include <string.h>


#define TIMER_NAME(TYPE, NAME, ...) #TYPE " " #NAME "(" #__VA_ARGS__ ") C"

#define HANDLE(TYPE, NAME, ...) \
  typedef TYPE (*NAME##_p) (__VA_ARGS__); \
  static NAME##_p NAME##_h = (NAME##_p)Tau_opencl_get_handle(#NAME)

#define HANDLE_AND_AUTOTIMER(TYPE, NAME, ...) \
  HANDLE(TYPE, NAME, __VA_ARGS__); \
  TAU_PROFILE(TIMER_NAME(TYPE, NAME, __VA_ARGS__), "", TAU_USER)

#define HANDLE_AND_TIMER(TYPE, NAME, ...) \
  HANDLE(TYPE, NAME, __VA_ARGS__); \
  TAU_PROFILE_TIMER(t, TIMER_NAME(TYPE, NAME, __VA_ARGS__), "", TAU_USER)


struct OpenCLGpuEvent : public GpuEvent
{
  cl_device_id id;
  x_uint64 commandId;
  cl_event event;
  const char *name;
  FunctionInfo *callingSite;
  GpuEventAttributes *gpu_event_attr;
  int number_of_gpu_events;
  int memcpy_type;
  double sync_offset;
  int taskId;

  ~OpenCLGpuEvent()
  {
    free(gpu_event_attr);
  }

  bool isMemcpy()
  {
    return memcpy_type != -1;
  }

  OpenCLGpuEvent(cl_device_id i, x_uint64 cId, double sync) :
  id(i), commandId(cId), event(NULL), name(NULL), sync_offset(sync), taskId(0), number_of_gpu_events(0)
  { }

  OpenCLGpuEvent *getCopy() const {
    OpenCLGpuEvent *c = new OpenCLGpuEvent(*this);
    return c;
  }

  bool less_than(const GpuEvent *other) const
  {
    if (this->id_p1() == other->id_p1())
    {
      return this->id_p2() < other->id_p2();
    }
    else
    {
      return this->id_p1() < other->id_p1();
    }
    //return strcmp(printId(), ((OpenCLGpuEvent *)o)->printId()) < 0;
  }

  const char *getName() const { return name; }
  int getTaskId() const { return taskId; }

  FunctionInfo *getCallingSite() const { 

    if (callingSite != NULL)
    {
      callingSite->SetPrimaryGroupName("TAU_REMOTE");
    }

    return callingSite; 
  }

  double syncOffset() const {
    return sync_offset;
  }

  // GPU attributes not implemented for OpenCL.
  void getAttributes(GpuEventAttributes *&gA, int &num) const
  {
    num = number_of_gpu_events;
    gA = gpu_event_attr;
  }

  void recordMetadata(int i) const {}

  /* CUDA Event are uniquely identified as the pair of two other ids:
   * context and call (API).
   */
  const char* gpuIdentifier() const
  {	
    char r[40];
    sprintf(r, "%d:%lld", id, commandId);
    return strdup(r);
  }

  x_uint64 id_p1() const { return (x_uint64) id; }
  x_uint64 id_p2() const { return (x_uint64) commandId; }
};

void * Tau_opencl_get_handle(char const * fnc_name);

void Tau_opencl_init();

void Tau_opencl_exit();

void Tau_opencl_enter_memcpy_event(const char *name, OpenCLGpuEvent *id, int size, int MemcpyType);

void Tau_opencl_exit_memcpy_event(const char *name, OpenCLGpuEvent *id, int MemcpyType);

void Tau_opencl_register_gpu_event(OpenCLGpuEvent *id, double start, double stop);

void Tau_opencl_register_memcpy_event(OpenCLGpuEvent *id, double start, double stop, int transferSize, int MemcpyType);

void Tau_opencl_enqueue_event(OpenCLGpuEvent * event);

void Tau_opencl_register_sync_event();

OpenCLGpuEvent * Tau_opencl_new_gpu_event(cl_command_queue queue, char const * name, int memcpy_type);

#endif /* __TAU_GPU_ADAPTER_OPENCL_H__ */

