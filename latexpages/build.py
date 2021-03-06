# build.py - compile parts, copy to output, combine, combine two_up

import os
import shutil
import multiprocessing

from . import jobs, render, pdfpages, tools

__all__ = ['make']


def make(config, procecesses=None, engine=None, cleanup=True):
    """Compile parts, copy, and combine as instructed in config file."""
    job = jobs.Job(config, engine, cleanup)
    pool = multiprocessing.Pool(procecesses)

    pool.map(compile_part, job.to_compile(), chunksize=1)

    copy_parts(job)

    pool.map(combine_parts, job.to_combine(), chunksize=1)

    pool.close()
    pool.join()


def compile_part(args):
    """Compile part LaTeX document to PDF."""
    job, part, filename, dvips = args
    with tools.chdir(job.config_dir, part):
        render.compile(filename,
            dvips=dvips, engine=job.engine, options=job.compile_opts)


def copy_parts(job):
    """Copy part PDFs to the output directory."""
    with tools.chdir(job.config_dir):
        if not os.path.isdir(job.directory):
            os.mkdir(job.directory)
        for source, target in job.to_copy():
            shutil.copyfile(source, target)


def combine_parts(args):
    """Combine output PDFs with pdfpages."""
    job, outname, template, prelims, filenames, two_up = args
    with tools.chdir(job.config_dir, job.directory):
        document = pdfpages.Source(prelims, filenames,
            job.context, template, job.includepdfopts,
            job.documentclass, job.documentopts)
        document.render(tools.swapext(outname, 'tex'),
            two_up=two_up, engine=job.engine, options=job.compile_opts,
            cleanup=job.cleanup)
