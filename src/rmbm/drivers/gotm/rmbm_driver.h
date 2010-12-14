#define RMBM_DIMENSIONS 1
#define RMBM_HORIZONTAL_IS_SCALAR

! Variable name and dimension specifyer for full bio fields
#define LOCATION kk
#define LOCATION_DIMENSIONS :

#define RMBM_MANAGE_DIAGNOSTICS
#define RMBM_SINGLE_STATE_VARIABLE_ARRAY
#define RMBM_USE_1D_LOOP

! Include RMBM preprocessor definitions.
! This *must* be done after the host-specific variables are defined (above),
! because these are used in rmbm.h.
#include "rmbm.h"

! Not used by RMBM itself; only by GOTM-RMBM driver gotm_rmbm.F90
#define LOCATION_RANGE 0:kk

