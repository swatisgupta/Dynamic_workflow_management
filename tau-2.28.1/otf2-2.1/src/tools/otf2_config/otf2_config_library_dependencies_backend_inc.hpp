#include <generate-library-dependencies-la-object.hpp>

static
void backend_dependency_1( std::deque<std::string>& libs, std::deque<std::string>& ldflags, std::deque<std::string>& rpaths, std::deque<std::string>& dependency_las, map< std::string, la_object>* la_objects )
{
    libs.clear();
    ldflags.clear();
    rpaths.clear();
    dependency_las.clear();
    libs.push_back( "-lrt" );
    libs.push_back( "-lm" );
    if ( la_objects->find( "libotf2" ) == la_objects->end() )
    {
        (*la_objects)[ "libotf2" ] =
            la_object( "libotf2",
                       "/homes/ssinghal/tau-2.28.1/otf2-2.1/build-backend",
                       "/lustre/ssinghal/tau2-install/x86_64/otf2-gcc/lib",
                       libs,
                       ldflags,
                       rpaths,
                       dependency_las );
    }
}

static
void add_library_dependencies_backend( std::deque<std::string>& libs, std::deque<std::string>& ldflags, std::deque<std::string>& rpaths, std::deque<std::string>& dependency_las, std::map< std::string, la_object>* la_objects )
{
    backend_dependency_1( libs, ldflags, rpaths, dependency_las, la_objects );
}
