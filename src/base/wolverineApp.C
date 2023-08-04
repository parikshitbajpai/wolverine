#include "wolverineApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "ModulesApp.h"
#include "MooseSyntax.h"

InputParameters
wolverineApp::validParams()
{
  InputParameters params = MooseApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  return params;
}

wolverineApp::wolverineApp(InputParameters parameters) : MooseApp(parameters)
{
  wolverineApp::registerAll(_factory, _action_factory, _syntax);
}

wolverineApp::~wolverineApp() {}

void 
wolverineApp::registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  ModulesApp::registerAllObjects<wolverineApp>(f, af, s);
  Registry::registerObjectsTo(f, {"wolverineApp"});
  Registry::registerActionsTo(af, {"wolverineApp"});

  /* register custom execute flags, action syntax, etc. here */
}

void
wolverineApp::registerApps()
{
  registerApp(wolverineApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
extern "C" void
wolverineApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  wolverineApp::registerAll(f, af, s);
}
extern "C" void
wolverineApp__registerApps()
{
  wolverineApp::registerApps();
}
