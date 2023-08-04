//* This file is part of the MOOSE framework
//* https://www.mooseframework.org
//*
//* All rights reserved, see COPYRIGHT for full restrictions
//* https://github.com/idaholab/moose/blob/master/COPYRIGHT
//*
//* Licensed under LGPL 2.1, please see LICENSE for details
//* https://www.gnu.org/licenses/lgpl-2.1.html
#include "wolverineTestApp.h"
#include "wolverineApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "MooseSyntax.h"

InputParameters
wolverineTestApp::validParams()
{
  InputParameters params = wolverineApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  return params;
}

wolverineTestApp::wolverineTestApp(InputParameters parameters) : MooseApp(parameters)
{
  wolverineTestApp::registerAll(
      _factory, _action_factory, _syntax, getParam<bool>("allow_test_objects"));
}

wolverineTestApp::~wolverineTestApp() {}

void
wolverineTestApp::registerAll(Factory & f, ActionFactory & af, Syntax & s, bool use_test_objs)
{
  wolverineApp::registerAll(f, af, s);
  if (use_test_objs)
  {
    Registry::registerObjectsTo(f, {"wolverineTestApp"});
    Registry::registerActionsTo(af, {"wolverineTestApp"});
  }
}

void
wolverineTestApp::registerApps()
{
  registerApp(wolverineApp);
  registerApp(wolverineTestApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
// External entry point for dynamic application loading
extern "C" void
wolverineTestApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  wolverineTestApp::registerAll(f, af, s);
}
extern "C" void
wolverineTestApp__registerApps()
{
  wolverineTestApp::registerApps();
}
